/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getFeedback = /* GraphQL */ `
  query GetFeedback($id: ID!) {
    getFeedback(id: $id) {
      id
      ContactId
      FeedbackType
      FeedbackDetails
      CallerTranscript
      CalleeTranscript
      Keyphrases
      SOP
      Jurisdiction
      createdAt
      updatedAt
    }
  }
`;
export const listFeedbacks = /* GraphQL */ `
  query ListFeedbacks(
    $filter: ModelFeedbackFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listFeedbacks(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        ContactId
        FeedbackType
        FeedbackDetails
        CallerTranscript
        CalleeTranscript
        Keyphrases
        SOP
        Jurisdiction
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
