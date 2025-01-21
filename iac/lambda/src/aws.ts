import SSM from "aws-sdk/clients/ssm";

const ssm = new SSM();

export function getSecret(key: string): Promise<string> {
    // aws's secret API is a bit annoying so we're wrapping it in a promise
    return new Promise((resolve, reject) => {
        ssm.getParameter({ Name: key, WithDecryption: true }, (err, data) => {
            if (err) {
                return reject(err);
            }
            if (data.Parameter && data.Parameter.Value && data.Parameter.Type == 'SecureString') {
                return resolve(data.Parameter.Value);
            } else {
                return reject('SecureString not provided or unsupported unencrypted String or StringList provided');
            }
        })
    });
}


