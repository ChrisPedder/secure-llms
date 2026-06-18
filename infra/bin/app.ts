#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SharedStack } from "../lib/shared-stack";

const app = new cdk.App();

new SharedStack(app, "SecureLlmsShared", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
