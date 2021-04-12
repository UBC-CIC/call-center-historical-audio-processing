import {Auth} from "aws-amplify";
import {Signer} from '@aws-amplify/core';
import {RestClient} from "@aws-amplify/api-rest";

const region = 'us-west-2';
const domain = 'search-transcript-indexer-zumaoft7xahmz2i7b4nxtqr6ge.us-west-2.es.amazonaws.com';
const index = 'transcripts';


export default async function indexDocument(contactId, document) {

    let esUrl = `https://${domain}/${index}/_doc/${contactId}`;
    let signedRequest = await signRequest(esUrl, document)
    let credentials = await Auth.currentCredentials();

    let restClient = new RestClient({
        credentials: credentials
    })
    console.log(signedRequest)


    let apiInfo = {
        endpoint: signedRequest.url,
        region: region,
        service: 'es'
    }

    let extraParams = {
        response: true,
        body: document,
        headers: signedRequest.headers
    }


    restClient.ajax(apiInfo, 'PUT', extraParams)
        .then(res=> console.log(res))
        .catch(err=> console.log(err))


    return signedRequest

    // let endpoint = new Endpoint(domain);
    // let request = new HttpRequest(endpoint, region);
    //
    // request.method = 'PUT';
    // request.path += index + '/' + type + '/' + contactId;
    // request.body = JSON.stringify(document);
    // request.headers['host'] = domain;
    // request.headers['Content-Type'] = 'application/json';


    // var signer = new Signer.V4(request, 'es');
    // signer.addAuthorization(credentials, new Date());
    //

    // signedRequest['endpoint'] = {
    //     hostname: domain,
    //     protocol: 'http',
    //     port: 443
    // }
    // signedRequest['path'] = {
    //     'path': `/${index}/_doc/${contactId}`
    // }
    //
    // console.log(signedRequest)
    // var client = new AWS.HttpClient();
    // client.handleRequest(signedRequest, null, function(response) {
    //     console.log(response.statusCode + ' ' + response.statusMessage);
    //     var responseBody = '';
    //     response.on('data', function (chunk) {
    //         responseBody += chunk;
    //     });
    //     response.on('end', function (chunk) {
    //         console.log('Response body: ' + responseBody);
    //     });
    // }, function(error) {
    //     console.log('Error: ' + error);
    // });
}

function signRequest(url, data) {
    return Auth.currentCredentials()
        .then(credentials => {
            let cred = Auth.essentialCredentials(credentials);
            return Promise.resolve(cred);
        })
        .then(essentialCredentials => {
            let params = {
                hostname: domain,
                headers: {
                    // 'Host': domain,
                    'Content-Type': 'application/json',
                    // 'Access-Control-Allow-Origin': '*',
                    // 'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
                    // 'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token'
                },
                body: JSON.stringify(data),
                method: 'PUT',
                url: url
            }

            // cred object keys should stay the same so that
            // Signer.sign function can access the keys
            let cred = {
                secret_key: essentialCredentials.secretAccessKey,
                access_key: essentialCredentials.accessKeyId,
                session_token: essentialCredentials.sessionToken
            }

            let serviceInfo = {
                region: region, service: 'es'
            }
            let signedReq = Signer.sign(params, cred, serviceInfo);
            return Promise.resolve(signedReq);
        });
}