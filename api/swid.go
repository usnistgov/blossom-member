package api

/*import (
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/usnistgov/blossom/chaincode/model"
)

type (
	// SwIDInterface provides the functions to interact with SwID tags in fabric.
	SwIDInterface interface {
		// ReportSwID is used by Agencies to report to Blossom when a software user has installed a piece of software associated
		// with a license that agency has out. This function will invoke NGAc chaincode to add the SwID to the NGAC graph.
		ReportSwID(ctx contractapi.TransactionContextInterface, swid *model.SwID) error

		// GetSwID returns the SwID object including the XML that matches the provided primaryTag parameter.
		GetSwID(ctx contractapi.TransactionContextInterface, primaryTag string) (*model.SwID, error)

		// GetLicenseSwIDs returns the primary tags of the SwIDs that are associated with the given license ID.
		GetLicenseSwIDs(ctx contractapi.TransactionContextInterface) ([]string, error)
	}
)

func NewSwIDContract() SwIDInterface {
	return &BlossomSmartContract{}
}

func (b *BlossomSmartContract) ReportSwID(ctx contractapi.TransactionContextInterface, swid *model.SwID) error {
	return nil
}

func (b *BlossomSmartContract) GetSwID(ctx contractapi.TransactionContextInterface, primaryTag string) (*model.SwID, error) {
	return &model.SwID{}, nil
}

func (b *BlossomSmartContract) GetLicenseSwIDs(ctx contractapi.TransactionContextInterface) ([]string, error) {
	return nil, nil
}
*/
