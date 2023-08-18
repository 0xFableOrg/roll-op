"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.sponsorTransaction = void 0;
const ethers_1 = require("ethers");
const abis_1 = require("./abis");
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
function sponsorTransaction(userOp) {
    var _a;
    return __awaiter(this, void 0, void 0, function* () {
        const paymasterAddress = process.env.PAYMASTER_ADDRESS;
        const provider = new ethers_1.ethers.JsonRpcProvider(process.env.RPC_URL);
        const signer = new ethers_1.ethers.Wallet(process.env.PRIVATE_KEY);
        const paymaster = new ethers_1.ethers.Contract(paymasterAddress, abis_1.paymasterAbi, provider);
        const coder = new ethers_1.ethers.AbiCoder();
        const validAfter = (_a = (yield provider.getBlock('latest'))) === null || _a === void 0 ? void 0 : _a.timestamp;
        // sanity check for validAfter
        if (validAfter === undefined)
            throw new Error('Could not get latest block timestamp');
        const validUntil = validAfter + 300; // 5 minutes
        const hash = yield paymaster.getHash(userOp, validUntil, validAfter);
        const signature = yield signer.signMessage(ethers_1.ethers.getBytes(hash));
        return Object.assign(Object.assign({}, userOp), { paymasterAndData: ethers_1.ethers.concat([
                paymasterAddress,
                coder.encode(['uint48', 'uint48'], [validUntil, validAfter]),
                signature
            ]) });
    });
}
exports.sponsorTransaction = sponsorTransaction;
