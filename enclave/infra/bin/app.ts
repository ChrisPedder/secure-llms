#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { EnclaveStack } from "../lib/enclave-stack";

const app = new cdk.App();

new EnclaveStack(app, "SecureLlmsEnclave", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
