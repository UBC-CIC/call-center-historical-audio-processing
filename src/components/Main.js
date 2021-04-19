import React from 'react';
import {withRouter} from 'react-router-dom';
import S3UploadForm from './S3UploadForm';
import Navbar from './Navbar';

class Main extends React.Component {

    render() {
        return (
            <div>
                <Navbar/>
                <S3UploadForm/>
            </div>
        );
    }
}

export default withRouter(Main);