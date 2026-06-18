import * as path from "path";

import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export class FheStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    cdk.Tags.of(this).add("Project", "secure-llms");
    cdk.Tags.of(this).add("SubProject", "fhe");

    const vpc = ec2.Vpc.fromLookup(this, "Vpc", {
      tags: { Project: "secure-llms" },
    });

    const bucket = new s3.Bucket(this, "DataBucket", {
      bucketName: `secure-llms-fhe-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const cluster = new ecs.Cluster(this, "Cluster", {
      vpc,
      clusterName: "secure-llms-fhe",
    });

    const logGroup = new logs.LogGroup(this, "LogGroup", {
      logGroupName: "/secure-llms/fhe",
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, "TaskDef", {
      memoryLimitMiB: 8192,
      cpu: 4096,
    });

    bucket.grantRead(taskDefinition.taskRole);

    const image = ecs.ContainerImage.fromAsset(
      path.join(__dirname, "..", "..", ".."),
    );

    taskDefinition.addContainer("fhe", {
      image,
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: "fhe",
      }),
      command: [
        "python",
        "-m",
        "src.run",
        "--data-path",
        `s3://${bucket.bucketName}/creditcard.csv`,
      ],
    });

    new cdk.CfnOutput(this, "BucketName", {
      value: bucket.bucketName,
      description: "S3 bucket for uploading creditcard.csv",
    });

    new cdk.CfnOutput(this, "ClusterArn", {
      value: cluster.clusterArn,
      description: "ECS cluster ARN for running the FHE task",
    });

    new cdk.CfnOutput(this, "TaskDefinitionArn", {
      value: taskDefinition.taskDefinitionArn,
      description: "Task definition ARN to use with aws ecs run-task",
    });

    new cdk.CfnOutput(this, "LogGroupName", {
      value: logGroup.logGroupName,
      description: "CloudWatch log group for FHE output",
    });

    const privateSubnets = vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
    });

    new cdk.CfnOutput(this, "PrivateSubnets", {
      value: privateSubnets.subnetIds.join(","),
      description: "Private subnet IDs for run-task network configuration",
    });
  }
}
