#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { FheStack } from "../lib/fhe-stack";

const app = new cdk.App();

new FheStack(app, "SecureLlmsFhe", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
