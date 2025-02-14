locals {
  BLOSSOM_NIST = {
  
    network_id            = "n-FLXXKM7INVCDXGQMUAH633E6PQ"
    network_name          = "Blossom"

    member_id             = "m-DTLKIKVWWZER3DUHQUDH43I7YQ"
    member_name           = "NIST"

    peer_node_id          = "nd-BURDFKAXHRFD3JHWFTPPPEJJ4M"

//    channel_name          = "blossom1"
//    contract_name         = "blossom"
    channel_name          = "authorization"
    contract_name         = "authorization"
    auth_channel          = "authorization"
    auth_contract         = "authorization"
    bus_channel           = "business"
    bus_contract          = "business"

    identities_ssm_prefix = "/nist/blossom/dev/user"
    cognito_domain_prefix = "blossom_test"
  }
}
