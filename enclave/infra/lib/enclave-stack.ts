import * as path from "path";

import * as cdk from "aws-cdk-lib";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as cw_actions from "aws-cdk-lib/aws-cloudwatch-actions";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as kms from "aws-cdk-lib/aws-kms";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambda_nodejs from "aws-cdk-lib/aws-lambda-nodejs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as sns from "aws-cdk-lib/aws-sns";
import * as sns_subscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import { Construct } from "constructs";

export class EnclaveStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    cdk.Tags.of(this).add("Project", "secure-llms");
    cdk.Tags.of(this).add("SubProject", "enclave");

    const vpc = ec2.Vpc.fromLookup(this, "Vpc", {
      tags: { Project: "secure-llms" },
    });

    // KMS RSA asymmetric key for client-side encryption
    const enclaveKey = new kms.Key(this, "EnclaveKey", {
      description: "RSA key for enclave message encryption/decryption",
      keySpec: kms.KeySpec.RSA_2048,
      keyUsage: kms.KeyUsage.ENCRYPT_DECRYPT,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    enclaveKey.addAlias("alias/secure-llms-enclave");

    // Security group: allow HTTPS inbound
    const sg = new ec2.SecurityGroup(this, "EnclaveSg", {
      vpc,
      description: "Enclave chatbot: HTTPS inbound",
      allowAllOutbound: true,
    });
    sg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), "HTTPS");
    sg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(8080), "Flask UI");

    // IAM role for the EC2 instance
    const role = new iam.Role(this, "InstanceRole", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore"),
      ],
    });

    // Allow GetPublicKey (no attestation needed — public key is not sensitive)
    enclaveKey.grant(role, "kms:GetPublicKey");

    // Allow Decrypt (in production, gate on attestation PCR values via key policy)
    enclaveKey.grant(role, "kms:Decrypt");

    // Allow Bedrock invoke
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      }),
    );

    // Allow CloudWatch metric publishing
    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ["cloudwatch:PutMetricData"],
        resources: ["*"],
        conditions: {
          StringEquals: { "cloudwatch:namespace": "SecureLlms/Enclave" },
        },
      }),
    );

    // EC2 instance with enclave support
    const instance = new ec2.Instance(this, "EnclaveInstance", {
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      instanceType: new ec2.InstanceType("c5.xlarge"),
      machineImage: ec2.MachineImage.latestAmazonLinux2023(),
      securityGroup: sg,
      role,
      associatePublicIpAddress: true,
    });

    // Enable Nitro Enclaves on the instance
    const cfnInstance = instance.node.defaultChild as ec2.CfnInstance;
    cfnInstance.enclaveOptions = { enabled: true };

    // User data script: install deps, build EIF, start services
    instance.addUserData(
      "#!/bin/bash",
      "set -euo pipefail",
      "",
      "# Install Nitro Enclaves CLI and allocator",
      "dnf install -y aws-nitro-enclaves-cli aws-nitro-enclaves-cli-devel docker python3.11 python3.11-pip git",
      "systemctl enable --now docker",
      "systemctl enable --now nitro-enclaves-allocator.service",
      "usermod -aG docker ec2-user",
      "usermod -aG ne ec2-user",
      "",
      "# Configure enclave allocator (2 vCPUs, 4GB for enclave)",
      "sed -i 's/memory_mib:.*/memory_mib: 4096/' /etc/nitro_enclaves/allocator.yaml",
      "sed -i 's/cpu_count:.*/cpu_count: 2/' /etc/nitro_enclaves/allocator.yaml",
      "systemctl restart nitro-enclaves-allocator.service",
      "",
      "# Install vsock-proxy",
      "dnf install -y aws-nitro-enclaves-cli",
      "",
      "# Clone the application code",
      `REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)`,
      "",
      "# Copy application files (in production, pull from S3 or ECR)",
      "mkdir -p /opt/enclave /opt/parent",
      "",
      "# Start vsock-proxy for KMS and Bedrock",
      `vsock-proxy 8000 kms.$REGION.amazonaws.com 443 &`,
      `vsock-proxy 8001 bedrock-runtime.$REGION.amazonaws.com 443 &`,
      "",
      "# Build the enclave image",
      "cd /opt/enclave",
      "docker build -t enclave-app -f Dockerfile .",
      "nitro-cli build-enclave --docker-uri enclave-app:latest --output-file enclave.eif",
      "",
      "# Start the enclave",
      "nitro-cli run-enclave --cpu-count 2 --memory 4096 --eif-path enclave.eif",
      "",
      "# Start the parent Flask server",
      "cd /opt/parent",
      "pip3.11 install flask boto3 cryptography",
      `export KMS_KEY_ID="${enclaveKey.keyId}"`,
      "export ENCLAVE_CID=16",
      "export ENCLAVE_PORT=5000",
      "python3.11 server.py &",
    );

    // CloudWatch log group for instance logs
    new logs.LogGroup(this, "LogGroup", {
      logGroupName: "/secure-llms/enclave",
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Auto-teardown: CloudWatch alarm → SNS → Lambda
    const topic = new sns.Topic(this, "TeardownTopic", {
      displayName: "Enclave auto-teardown",
    });

    const metric = new cloudwatch.Metric({
      namespace: "SecureLlms/Enclave",
      metricName: "LastRequestTimestamp",
      statistic: "Maximum",
      period: cdk.Duration.minutes(5),
    });

    const alarm = new cloudwatch.Alarm(this, "InactivityAlarm", {
      metric,
      threshold: 1,
      evaluationPeriods: 6,
      comparisonOperator:
        cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.BREACHING,
      alarmDescription:
        "Triggers when no chat requests received for 30 minutes",
    });

    alarm.addAlarmAction(new cw_actions.SnsAction(topic));

    const teardownFn = new lambda_nodejs.NodejsFunction(this, "TeardownFn", {
      entry: path.join(__dirname, "teardown-lambda", "index.ts"),
      handler: "handler",
      runtime: lambda.Runtime.NODEJS_20_X,
      timeout: cdk.Duration.seconds(30),
      environment: {
        INSTANCE_ID: instance.instanceId,
      },
    });

    teardownFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["ec2:StopInstances"],
        resources: [
          `arn:aws:ec2:${this.region}:${this.account}:instance/${instance.instanceId}`,
        ],
      }),
    );
    topic.addSubscription(
      new sns_subscriptions.LambdaSubscription(teardownFn),
    );

    // Outputs
    new cdk.CfnOutput(this, "InstancePublicIp", {
      value: instance.instancePublicIp,
      description: "Public IP of the enclave EC2 instance",
    });

    new cdk.CfnOutput(this, "InstanceId", {
      value: instance.instanceId,
      description: "EC2 instance ID",
    });

    new cdk.CfnOutput(this, "KmsKeyId", {
      value: enclaveKey.keyId,
      description: "KMS RSA key ID for client-side encryption",
    });

    new cdk.CfnOutput(this, "KmsKeyArn", {
      value: enclaveKey.keyArn,
      description: "KMS RSA key ARN",
    });
  }
}
