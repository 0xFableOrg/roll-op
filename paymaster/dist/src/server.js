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
const express_1 = __importDefault(require("express"));
const body_parser_1 = __importDefault(require("body-parser"));
const rpcMethods_1 = require("./rpcMethods");
const app = (0, express_1.default)();
const port = 3000;
app.use(body_parser_1.default.json());
app.post('/', (req, res) => __awaiter(void 0, void 0, void 0, function* () {
    const { id, method, params } = req.body;
    if (method === 'pm_sponsorUserOperation') {
        try {
            const userOp = yield (0, rpcMethods_1.sponsorTransaction)(params);
            res.send({
                jsonrpc: '2.0',
                id,
                result: userOp
            });
        }
        catch (err) {
            res.send({
                jsonrpc: '2.0',
                id,
                error: err
            });
        }
        return;
    }
    res.send({
        jsonrpc: '2.0',
        id,
        result: 'No valid reponse'
    });
}));
app.listen(port, () => {
    console.log(`JSON-RPC server is running on port ${port}`);
});
