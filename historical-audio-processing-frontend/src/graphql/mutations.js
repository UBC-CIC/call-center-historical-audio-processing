/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const createTranscript = /* GraphQL */ `
  mutation CreateTranscript(
    $input: CreateTranscriptInput!
    $condition: ModelTranscriptConditionInput
  ) {
    createTranscript(input: $input, condition: $condition) {
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
export const updateTranscript = /* GraphQL */ `
  mutation UpdateTranscript(
    $input: UpdateTranscriptInput!
    $condition: ModelTranscriptConditionInput
  ) {
    updateTranscript(input: $input, condition: $condition) {
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
export const deleteTranscript = /* GraphQL */ `
  mutation DeleteTranscript(
    $input: DeleteTranscriptInput!
    $condition: ModelTranscriptConditionInput
  ) {
    deleteTranscript(input: $input, condition: $condition) {
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
