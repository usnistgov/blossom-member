import {
    Context,
    APIGatewayProxyCallback,
    APIGatewayEvent,
} from 'aws-lambda';
import { HandlerFunc, invokeHandler, queryHandler, pinError, pinLocation } from './handlers';
const THIS_FILE = 'index.ts';
/**
 * 
 * @param event AWS gateway event
 * @param context BloSS🌻M context to properly dispatch event with more details
 * @param callback Gateway callback to communicate returned information
 */
export const handler = async (
    event: APIGatewayEvent,
    context: Context,
    callback: APIGatewayProxyCallback
) => {
    console.log(`${pinLocation(THIS_FILE)}: ${JSON.stringify(event, null, 2)}`);
    console.log(`${pinLocation(THIS_FILE)}: ${JSON.stringify(context, null, 2)}`);


    const bodyJson = JSON.parse(event.body ?? '');
    console.log(`index.ts-L24: ${bodyJson['functionType']}`);
    console.log(`index.ts-L25: ${JSON.stringify(context, null, 2)}`);
    let handlerFunc: HandlerFunc;
    switch (bodyJson['functionType']) {
        case 'query':
            handlerFunc = queryHandler;
            break;
        case 'invoke':
            handlerFunc = invokeHandler;
            break;
        default:
            throw new Error(`${pinError(new Error())} Request body "functionType" must be one of "query" or "invoke"`);
    }

    try {
        const result = await handlerFunc(event, bodyJson);
        callback(null, result);
    } catch (error) {
        callback(`${pinError(new Error())} ${error}`);
    }
};
