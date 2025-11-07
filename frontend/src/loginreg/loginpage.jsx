import './loginreg.css';
import { auth } from "./firebase";
import { signInWithEmailAndPassword } from "firebase/auth";
import { useState } from 'react';

function Login({onRegister, onSuccess, onForgot}) {
    const [email, setEmail] = useState(""); 
    const [pword, setPword] = useState("");
    async function manageLogin(e){ 
        e.preventDefault();
        try {
            await signInWithEmailAndPassword(auth, email, pword);
            alert("Login successful!"); 
            onSuccess();
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
                <p className='title'>Login</p>
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
                <button className='userButton'type="submit">Login</button>
                <div className='butContainer'>
                    <p className='regLink'>Don't have an account? <button className="clickLink" onClick={onRegister}>click here</button></p>
                    <p className='regLink'>Forgot Password? <button className='clickLink' onClick={onForgot}>click here</button></p>
                </div>
            </form>
        </div>
    );
}

export default Login;

