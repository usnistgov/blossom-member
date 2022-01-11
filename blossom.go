package main

import (
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric/core/chaincode/shim"
	"github.com/hyperledger/fabric/protos/peer"
	"github.com/usnistgov/blossom/chaincode/adminmsp"
	"github.com/usnistgov/blossom/chaincode/ngac/pdp"
)

type BlossomSmartContract struct{}

// main function starts up the chaincode in the container during instantiate
func main() {
	if err := shim.Start(new(BlossomSmartContract)); err != nil {
		fmt.Printf("Error starting Blossom chaincode: %s", err)
	}
}

func (b *BlossomSmartContract) Init(_ shim.ChaincodeStubInterface) peer.Response {
	return shim.Success([]byte(fmt.Sprintf("Admin MSPID is %s. ", adminmsp.AdminMSP)))
}

func (b *BlossomSmartContract) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	fn, args := stub.GetFunctionAndParameters()

	var (
		result []byte
		err    error
	)

	switch fn {
	case "InitNGAC":
		err = b.handleInitNGAC(stub)
	case "RequestAccount":
		err = b.handleRequestAccount(stub)
	case "ApproveAccount":
		err = b.handleApproveAccount(stub, args)
	case "UploadATO":
		err = b.handleUploadATO(stub)
	case "UpdateAccountStatus":
		err = b.handleUpdateAccountStatus(stub, args)
	case "Accounts":
		result, err = b.handleAccounts(stub)
	case "Account":
		result, err = b.handleAccount(stub, args)
	case "OnboardAsset":
		err = b.handleOnboardAsset(stub, args)
	case "OffboardAsset":
		err = b.handleOffboardAsset(stub, args)
	case "Assets":
		result, err = b.handleAssets(stub)
	case "AssetInfo":
		result, err = b.handleAssetInfo(stub, args)
	case "RequestCheckout":
		err = b.handleRequestCheckout(stub)
	case "CheckoutRequests":
		result, err = b.handleCheckoutRequests(stub, args)
	case "ApproveCheckout":
		err = b.handleApproveCheckout(stub)
	case "Licenses":
		result, err = b.handleLicenses(stub, args)
	case "InitiateCheckin":
		err = b.handleInitiateCheckin(stub)
	case "ProcessCheckin":
		err = b.handleProcessCheckin(stub)
	case "ReportSwID":
		err = b.handleReportSwID(stub)
	case "DeleteSwID":
		err = b.handleDeleteSwID(stub)
	case "GetSwID":
		result, err = b.handleGetSwID(stub)
	case "GetSwIDsAssociatedWithAsset":
		result, err = b.handleGetSwIDsAssociatedWithAsset(stub, args)
	case "test":
		result = []byte(args[0])
	case "GetHistory":
		result, err = b.handleGetHistory(stub, args)
	}

	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(result)
}

func (b *BlossomSmartContract) handleInitNGAC(stub shim.ChaincodeStubInterface) error {
	return pdp.InitCatalogNGAC(stub, CatalogCollection())
}

func (b *BlossomSmartContract) handleGetHistory(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	if len(args) < 1 {
		return nil, fmt.Errorf("incorrect number of arguments, expecting 1")
	}

	accountName := args[0]

	history, err := b.GetHistory(stub, accountName)
	if err != nil {
		return nil, err
	}

	return json.Marshal(history)
}

func (b *BlossomSmartContract) handleRequestAccount(stub shim.ChaincodeStubInterface) error {
	return b.RequestAccount(stub)
}

func (b *BlossomSmartContract) handleApproveAccount(stub shim.ChaincodeStubInterface, args []string) error {
	account := args[0]
	return b.ApproveAccount(stub, account)
}

func (b *BlossomSmartContract) handleUploadATO(stub shim.ChaincodeStubInterface) error {
	return b.UploadATO(stub)
}

func (b *BlossomSmartContract) handleUpdateAccountStatus(stub shim.ChaincodeStubInterface, args []string) error {
	accountName := args[0]
	status := args[1]

	return b.UpdateAccountStatus(stub, accountName, status)
}

func (b *BlossomSmartContract) handleAccounts(stub shim.ChaincodeStubInterface) ([]byte, error) {
	accounts, err := b.Accounts(stub)
	if err != nil {
		return nil, err
	}

	return json.Marshal(accounts)
}

func (b *BlossomSmartContract) handleAccount(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	accountName := args[0]

	account, err := b.Account(stub, accountName)
	if err != nil {
		return nil, err
	}

	return json.Marshal(account)
}

func (b *BlossomSmartContract) handleOnboardAsset(stub shim.ChaincodeStubInterface, args []string) error {
	id := args[0]
	name := args[1]
	onboardDate := args[2]
	exp := args[3]

	return b.OnboardAsset(stub, id, name, onboardDate, exp)
}

func (b *BlossomSmartContract) handleOffboardAsset(stub shim.ChaincodeStubInterface, args []string) error {
	assetID := args[0]
	return b.OffboardAsset(stub, assetID)
}

func (b *BlossomSmartContract) handleAssets(stub shim.ChaincodeStubInterface) ([]byte, error) {
	assets, err := b.Assets(stub)
	if err != nil {
		return nil, err
	}

	return json.Marshal(assets)
}

func (b *BlossomSmartContract) handleAssetInfo(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	assetID := args[0]

	asset, err := b.AssetInfo(stub, assetID)
	if err != nil {
		return nil, err
	}

	return json.Marshal(asset)
}

func (b *BlossomSmartContract) handleRequestCheckout(stub shim.ChaincodeStubInterface) error {
	return b.RequestCheckout(stub)
}

func (b *BlossomSmartContract) handleCheckoutRequests(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	account := args[0]

	requests, err := b.CheckoutRequests(stub, account)
	if err != nil {
		return nil, err
	}

	return json.Marshal(requests)
}

func (b *BlossomSmartContract) handleApproveCheckout(stub shim.ChaincodeStubInterface) error {
	return b.ApproveCheckout(stub)
}

func (b *BlossomSmartContract) handleLicenses(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	assetID := args[0]

	result, err := b.Licenses(stub, assetID)
	if err != nil {
		return nil, err
	}

	return json.Marshal(result)
}

func (b *BlossomSmartContract) handleInitiateCheckin(stub shim.ChaincodeStubInterface) error {
	return b.InitiateCheckin(stub)
}

func (b *BlossomSmartContract) handleProcessCheckin(stub shim.ChaincodeStubInterface) error {
	return b.ProcessCheckin(stub)
}

func (b *BlossomSmartContract) handleReportSwID(stub shim.ChaincodeStubInterface) error {
	return b.ReportSwID(stub)
}

func (b *BlossomSmartContract) handleDeleteSwID(stub shim.ChaincodeStubInterface) error {
	return b.DeleteSwID(stub)
}

func (b *BlossomSmartContract) handleGetSwID(stub shim.ChaincodeStubInterface) ([]byte, error) {
	swid, err := b.GetSwID(stub)
	if err != nil {
		return nil, err
	}

	return json.Marshal(swid)
}

func (b *BlossomSmartContract) handleGetSwIDsAssociatedWithAsset(stub shim.ChaincodeStubInterface, args []string) ([]byte, error) {
	account := args[0]
	assetID := args[1]

	swids, err := b.GetSwIDsAssociatedWithAsset(stub, account, assetID)
	if err != nil {
		return nil, err
	}

	return json.Marshal(swids)
}
