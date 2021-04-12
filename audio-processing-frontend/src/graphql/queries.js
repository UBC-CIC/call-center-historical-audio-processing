/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getTranscript = /* GraphQL */ `
  query GetTranscript($id: ID!) {
    getTranscript(id: $id) {
      id
      description
      jurisdiction
      fileType
      fileName
      procedure
      fileData {
        bucketName
        bucketKey
      }
      expireTime
      createdAt
      updatedAt
    }
  }
`;
export const listTranscripts = /* GraphQL */ `
  query ListTranscripts(
    $filter: ModelTranscriptFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listTranscripts(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        description
        jurisdiction
        fileType
        fileName
        procedure
        fileData {
          bucketName
          bucketKey
        }
        expireTime
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
