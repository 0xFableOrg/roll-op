import { ethers } from 'ethers';
import dotenv from 'dotenv';
import { paymasterAbi } from '../src/abis';
dotenv.config();

async function main() {
    const depositAmount = process.env.INITIAL_DEPOSIT as string;
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL as string);
    const signer = new ethers.Wallet(process.env.PRIVATE_KEY as string, provider);

    // Paymaster first needs to have funds in Entrypoint contract
    const paymasterAddress = process.env.PAYMASTER_ADDRESS as string;
    const paymaster = new ethers.Contract(
        paymasterAddress,
        paymasterAbi,
        signer
    );

    // Deposit
    await (await paymaster.deposit({ value: ethers.parseEther(depositAmount)})).wait();
    await (await paymaster.addStake(3000, { value: ethers.parseEther(depositAmount)})).wait();

    console.log("Deposit funds successful!");
}

main();