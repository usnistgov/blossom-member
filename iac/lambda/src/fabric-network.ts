import { Gateway, Wallets } from 'fabric-network';
import YAML from 'yaml';
import { getSecret } from './aws';
import { pinLocation } from './handlers';
const THIS_FILE = "fabric-network.ts";

async function buildIdentity(username: string) {
    console.log(`${pinLocation('Building-Identity (ASYNC) ' + THIS_FILE)}:`+
    `\n\tUSER: ${username};` +
    `\n\tPREF-X: ${process.env.SSM_PREFIX}`);
    
    const identity = {
        credentials: {
            certificate: await getSecret(`${process.env.SSM_PREFIX}/${username}/cert`),
            privateKey: await getSecret(`${process.env.SSM_PREFIX}/${username}/pk`),
        },
        mspId: await getSecret(`${process.env.SSM_PREFIX}/${username}/mspId`),
        type: 'X.509'
    };
    const wallet = await Wallets.newInMemoryWallet();
    wallet.put(username, identity);
    return { wallet, identity };
}

export async function setupNetwork(username: string, channel: string) {
    const { identity, wallet } = await buildIdentity(username);

    const profile_raw = process.env.PROFILE_ENCODED;
    if (profile_raw === undefined) {
        throw new Error('The connection profile was not provided via the "PROFILE_ENCODED" env var');
    }

    const profile = YAML.parse(Buffer.from(profile_raw, 'base64').toString());
    profile.network_name='Blossom';
    console.log(`Profile:\n ${JSON.stringify(profile)}`);
    console.log(`${pinLocation('Building-Identity (ASYNC) ' + THIS_FILE)}:` +
        `\n\tWALLET: ${JSON.stringify(wallet, null, 2)};` +
        `\n\tID: ${JSON.stringify(identity, null, 2)}`);
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
