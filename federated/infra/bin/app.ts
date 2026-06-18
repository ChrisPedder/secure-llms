#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { FederatedStack } from "../lib/federated-stack";

const app = new cdk.App();

new FederatedStack(app, "SecureLlmsFederated", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
