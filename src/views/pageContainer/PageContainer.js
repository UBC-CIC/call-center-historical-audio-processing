import React from 'react';
import {Grid} from "semantic-ui-react";
import Navbar from "../../components/navbar/Navbar";
import logo from "../../logo.svg";
import S3UploadForm from "../../components/S3UploadForm";

function PageContainer(props) {
    return (
        <div>
        {/*<Grid className="App" style={{width: "100vw", height: "100vh"}}>*/}
            <Navbar/>
            <S3UploadForm/>
        {/*</Grid>*/}
        </div>
    )
}

export default PageContainer;