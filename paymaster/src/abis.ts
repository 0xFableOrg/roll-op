import * as fs from 'fs';

function readFile(path: string) {
    try {
        // Read the JSON file synchronously and store its contents in a variable
        const jsonData = fs.readFileSync(path, 'utf8');
  
        // Parse the JSON data into an object
        const jsonObject = JSON.parse(jsonData);

        return jsonObject["abi"]
    } catch (error) {
        console.error('Error reading/parsing JSON file:', error);
    }
}

const basePath = "../account-abstraction/artifacts/contracts"

export const simpleAccountAbi 
    = readFile(basePath + "/samples/SimpleAccount.sol/SimpleAccount.json");

export const simpleAccountFactoryAbi 
    = readFile(basePath + "/samples/SimpleAccountFactory.sol/SimpleAccountFactory.json");

export const paymasterAbi
    = readFile(basePath + "/samples/VerifyingPaymaster.sol/VerifyingPaymaster.json");

export const entrypointAbi 
    = readFile(basePath + "/core/EntryPoint.sol/EntryPoint.json");