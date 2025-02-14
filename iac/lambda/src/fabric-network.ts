import { Gateway, Wallets } from 'fabric-network';
import YAML from 'yaml';
import { getSecret } from './aws';
import { pinLocation } from './handlers';
const THIS_FILE = "fabric-network.ts";
const today='2025-01-28 -@- 12:59'
/**
 * 
 * @param username: Cognito-AMB username to pull up SSM data for connection and identity
 * @returns object packed with AMB Wallet and AMB Identity
 */
async function buildIdentity(username: string) {
    console.log(`${pinLocation('Building-Identity (ASYNC) ' + THIS_FILE)}@${today}:`+
    `\n\tUSER: ${username};` +
    `\n\tPREF-X: ${process.env.SSM_PREFIX}`);

    const user_cert = await getSecret(`${process.env.SSM_PREFIX}/${username}/cert`);
    const user_key = await getSecret(`${process.env.SSM_PREFIX}/${username}/pk`);
    const identity = {
        credentials: {
            certificate: user_cert,
            privateKey: user_key,
        },
        mspId: await getSecret(`${process.env.SSM_PREFIX}/${username}/mspId`),
        type: 'X.509'
    };
    
    const wallet = await Wallets.newInMemoryWallet();
    await wallet.put(username, identity);
    return { identity, wallet };
}

/**
 * 
 * @param {*} username: Cognito-AMB username to pull up SSM data for connection and identity
 * @param {*} channel 
 * @returns 
 */
export async function setupNetwork(username: string, channel: string) {
    // Build Identity+Wallet by User Name
    const { identity, wallet } = await buildIdentity(username);

    // Bail out quickly if Profile was not specified in the Lambda's Environment 
    const profile_raw = process.env.PROFILE_ENCODED;
    if (profile_raw === undefined) {
        throw new Error('The connection profile was not provided via the "PROFILE_ENCODED" env var');
    }

    // Decode and parse profile information
    const profile = YAML.parse(Buffer.from(profile_raw, 'base64').toString());
    profile.network_name='Blossom';
    
    console.log(`${pinLocation('Building-Identity (ASYNC) ' + THIS_FILE)}@${today}:`
        +`\n\tProfile:\n ${JSON.stringify(profile)}`);
    console.log(`${pinLocation('Building-Identity (ASYNC) ' + THIS_FILE)}@${today}:` +
        `\n\tID: ${JSON.stringify(identity, null, 2)}` +
        `\n\tWALLET: ${JSON.stringify(wallet, null, 2)};`        
        );

    const gateway = new Gateway();
    await gateway.connect(profile, {
        wallet,
        identity,
        discovery: {
            asLocalhost: false,
            enabled: false,
        },
        // No handler strategy prevents the transaction submit from hanging
        eventHandlerOptions: {
            commitTimeout: 100,
            strategy: null
        }
    });

    return await gateway.getNetwork(channel);
}
