import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export class SharedStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    cdk.Tags.of(this).add("Project", "secure-llms");

    const vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        {
          name: "Public",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });

    new cdk.CfnOutput(this, "VpcId", {
      value: vpc.vpcId,
      exportName: "SecureLlmsVpcId",
    });

    new cdk.CfnOutput(this, "PublicSubnetIds", {
      value: vpc.publicSubnets.map((s) => s.subnetId).join(","),
      exportName: "SecureLlmsPublicSubnetIds",
    });

    new cdk.CfnOutput(this, "PrivateSubnetIds", {
      value: vpc.privateSubnets.map((s) => s.subnetId).join(","),
      exportName: "SecureLlmsPrivateSubnetIds",
    });
  }
}
