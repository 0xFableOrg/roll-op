## Paymaster

This is a barebone verifying paymaster server. It is meant to be used in conjuction with the `VerifyingPaymaster` [contract](https://github.com/eth-infinitism/account-abstraction/blob/develop/contracts/samples/VerifyingPaymaster.sol) by ETH Infinitism.

The flow for sponsoring a user's transaction as follows:
1. Users send a JSON RPC request to the paymaster server with the corresponding UserOp.
2. The paymaster server signs the hash of the UserOp if it decides to sponsor the transaction. The signature is encoded in the `paymasterAndData` field of the userOp.
3. The paymaster server sends the updated UserOp back to the user.
4. The user can now send the UserOp to the bundler and the transaction will be sponsored by the paymaster.

The encoding of `paymaster` as follows:
* First 20 bytes: paymaster smart contract address
* Next 64 bytes: 32 bytes each for `validUntil` and `validAfter`, these are `uint48` values for the time validity of the paymaster signature
* Final 65 bytes: the signature of the paymaster server on the hash of the UserOp


### Adding custom sponsor logic for paymaster

Developers could add custom logic to define what type of transactions to sponsor in the `src/rpcMethods.ts` file.

### Running tests

Once the bundler and paymaster server are running, run the tests with `pnpm run test`.