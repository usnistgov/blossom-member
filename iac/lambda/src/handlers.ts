import { APIGatewayEvent, APIGatewayProxyResult } from "aws-lambda";
import { setupNetwork } from "./fabric-network";
import { error } from "console";
import { int } from "aws-sdk/clients/datapipeline";

// const CHANNEL_NAME = process.env.CHANNEL_NAME ?? 'acquisition';
// const CONTRACT_NAME = process.env.CONTRACT_NAME ?? 'blossom';
const CHANNEL_NAME = process.env.CHANNEL_NAME ?? 'authorization';
const CONTRACT_NAME = process.env.CONTRACT_NAME ?? 'authorization';
const AUTH_CHANNEL = process.env.AUTH_CHANNEL ?? 'authorization';
const AUTH_CONTRACT = process.env.AUTH_CONTRACT  ?? 'authorization';
const BUS_CHANNEL = process.env.BUS_CHANNEL ?? "business" ;
const BUS_CONTRACT = process.env.BUS_CONTRACT ?? "business";
const THIS_FILE = "handlers.ts";

export type HandlerFunc = (event: APIGatewayEvent, bodyJson: any) => Promise<APIGatewayProxyResult>;

/**
 * 
 * @param error - The external error if present
 * @returns Descriptor of the error location
 */
function pinErrorMsg(error: any = undefined, depth: int = 2):string {  
    const index = (!error ? 2 : ((depth>=0)?depth:1))
    const e = !error ? new Error(): error;
    const regex = /\((.*):(\d+):(\d+)\)$/
    if(e.stack){
        const match = regex.exec(e.stack.split("\n")[index]);
        if (match){
            return `File: ${match[1]} @Ln:${match[2]} Col:${match[3]}\n`;
        }
    }
    return `Couldn't locate Error`
    // return {filepath: match[1], line: match[2],column: match[3]};
  }
/** Provides placement information for the location of the message and origin of the log entry
 *
 * @param specialPrefix - Additional prefix if needed
 * @param depth (default=2) stack diving depth - 2 will point to the correct place
 * @returns String with the CALLERS "FILE: LINE: Col:" location
 */
function pinLocationMsg(specialPrefix = '', depth = 2) {
    const index = (!specialPrefix ? 2 : ((depth >= 0) ? depth : 1));
    const error = new Error();
    const regex = /\((.*):(\d+):(\d+)\)$/;
    if (error.stack) {
        const match = regex.exec(error.stack.split("\n")[index]);
        if (match) {
            return `${specialPrefix ? specialPrefix + '-' : '@'}File: ${match[1]} @Line:${match[2]} Col:${match[3]}\n`;
        }
    }
    return `No Location Found for Caller in Trace-Stack`;
    // return {filepath: match[1], line: match[2],column: match[3]};
}
/**
 * Returns user name from event
 * @param event Original AWS API-GAteway Event
 * @returns User-Name as string
 */
function getUsername(event: APIGatewayEvent): string {
    const username = event.requestContext.authorizer?.claims.username;
    if (username === undefined || username === null) {
        const error = new Error(  `${pinErrorMsg(new Error())} Could not get username from requestContext`
                           +` (got ${JSON.stringify(event.requestContext.authorizer)})`);
        throw error;
    }
    return username as string;
}

type TransactionRequestBody = {
    function:string;
    functionType:string;
    args: string[];
    // optional in the latest API version
    channel?: string;
    contract?: string;
    functionName?: string;
    transient?: Record<string, string>;
    // Added for debugging
    transaction?:string;
    name?:string;
}

/**
 * Convert string-string map to string-buffer
 * @param transient Request part to convert into buffer
 * @returns buffer-converted object
 */
function convertTransientToBuffer(transient: Record<string, string>) {
    return Object.keys(transient).reduce<{
        [key: string]: Buffer;
    }>((acc, key) => {
        acc[key] = Buffer.from(transient[key]);
        return acc;
    }, {})
}

/**
 * 
 * @param event 
 * @param bodyJson 
 * @param type 
 * @returns 
 */
const transactionHandler = async (event: APIGatewayEvent, bodyJson: any, type: 'query' | 'invoke'): ReturnType<HandlerFunc> => {
    console.log('Ln83: Getting username...');
    const body = bodyJson as TransactionRequestBody;

    body.channel = CHANNEL_NAME;
    body.contract = CONTRACT_NAME;
    body.functionName =  !body.function?'account:getAccounts': body.function;
    body.name = "getAccounts";
    body.transaction = "dValue";    
    const username = getUsername(event);
    console.log(`${pinLocation('Setting up Transaction... ')} \n ${JSON.stringify(body, null, 2)}`);
    console.log(`${pinLocation('Setting up network... ')} on channel ${body.channel} for User: ${username}`);

    const network = await setupNetwork(username, body.channel);
    console.log('Ln96: Setting up contract...');
    console.log(`ln97: Setting up Transaction...\n${body}`);

    const transaction = network.getContract(body.contract).createTransaction(body.functionName);

    console.log(`ln101 Setting up Transaction...\n${body}`);

    if (body.transient) {
        transaction.setTransient(convertTransientToBuffer(body.transient));
    }

    transaction.setEndorsingOrganizations(network.getGateway().getIdentity().mspId);
    console.log('Evaluating/submitting transaction...');
    try {
        let result;
        if (type === 'query') {
            result = await transaction.evaluate(...body.args);
        } else {
            result = await transaction.submit(...body.args);
        }
        return {
            body: result.toString(),
            headers: {
                'Content-Type': 'application/json'
            },
            statusCode: 200
        };
    } catch (e) {
        return {
            body: `${pinErrorMsg(e)} Error: ${e}`,
            headers: {},
            statusCode: 500,
        }
    } finally {
        network.getGateway().disconnect();
    }
}

export const queryHandler: HandlerFunc = (event, bodyJson) => transactionHandler(event, bodyJson, 'query');
export const invokeHandler: HandlerFunc = (event, bodyJson) => transactionHandler(event, bodyJson, 'invoke');
export const pinError = (error: any)=> pinErrorMsg(error);
export const pinLocation = (message: string) => pinLocationMsg(message);