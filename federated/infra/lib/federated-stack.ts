import * as path from "path";

import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export class FederatedStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    cdk.Tags.of(this).add("Project", "secure-llms");
    cdk.Tags.of(this).add("SubProject", "federated");

    const vpc = ec2.Vpc.fromLookup(this, "Vpc", {
      tags: { Project: "secure-llms" },
    });

    const cluster = new ecs.Cluster(this, "Cluster", {
      vpc,
      clusterName: "secure-llms-federated",
    });

    const logGroup = new logs.LogGroup(this, "LogGroup", {
      logGroupName: "/secure-llms/federated",
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, "TaskDef", {
      memoryLimitMiB: 4096,
      cpu: 2048,
    });

    const image = ecs.ContainerImage.fromAsset(
      path.join(__dirname, "..", ".."),
      { exclude: ["infra", ".venv", "__pycache__", "data"] },
    );

    taskDefinition.addContainer("federated", {
      image,
      logging: ecs.LogDrivers.awsLogs({
        logGroup,
        streamPrefix: "federated",
      }),
    });

    new cdk.CfnOutput(this, "ClusterArn", {
      value: cluster.clusterArn,
      description: "ECS cluster ARN for running the federated training task",
    });

    new cdk.CfnOutput(this, "TaskDefinitionArn", {
      value: taskDefinition.taskDefinitionArn,
      description: "Task definition ARN to use with aws ecs run-task",
    });

    new cdk.CfnOutput(this, "LogGroupName", {
      value: logGroup.logGroupName,
      description: "CloudWatch log group for training output",
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
