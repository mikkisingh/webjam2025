import './loginreg.css';
import { auth } from "./firebase.jsx";
import { createUserWithEmailAndPassword} from "firebase/auth";
import { useState } from 'react';

function Register({ onLogin }){
    const [email, setEmail] = useState(""); 
    const [pword, setPword] = useState("");
    async function manageLogin(e){ 
        e.preventDefault();
        try {
            await createUserWithEmailAndPassword(auth, email, pword);
            alert("Creation Succesful!"); 
        } catch (loginError) { 
            alert(loginError.message);
        }
    };
    function setTheEmail(e){
        setEmail(e.target.value);
    };
    function setThePword(e){
        setPword(e.target.value);
    };
    return (
        <div className='pageBkg'>
            <form onSubmit={manageLogin} className='inputBlock'>
                <p className='title'>Register</p>
                <input
                    className='emailInput'
                    type="email"
                    value={email}
                    onChange={setTheEmail}
                    placeholder="Enter Email"
                />
                <input
                    className='pwordInput'
                    type="password"
                    value={pword}
                    onChange={setThePword}
                    placeholder="Enter Password"
                />
                <button className='userButton'type="submit">Register</button>
                <div className='butContainer'>
                    <p className='regLink'>Already have an account? <button className='clickLink' onClick={onLogin}>click here</button></p>
                </div>
            </form>
        </div>
    );
}

export default Register;

