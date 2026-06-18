import { EC2Client, StopInstancesCommand } from "@aws-sdk/client-ec2";

const ec2 = new EC2Client({});

export const handler = async (_event: Record<string, unknown>): Promise<void> => {
  const instanceId = process.env.INSTANCE_ID;
  if (!instanceId) {
    throw new Error("INSTANCE_ID environment variable not set");
  }

  console.log(`Stopping instance ${instanceId} due to inactivity`);
  await ec2.send(new StopInstancesCommand({ InstanceIds: [instanceId] }));
  console.log(`Instance ${instanceId} stop initiated`);
};
