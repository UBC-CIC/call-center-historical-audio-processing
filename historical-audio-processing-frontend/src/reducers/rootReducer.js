import { combineReducers } from 'redux';
import {authentication} from './AuthenticationReducer';

const rootReducer = combineReducers({
    authentication,
});

export default rootReducer;