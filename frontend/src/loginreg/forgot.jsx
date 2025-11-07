import { auth } from "./firebase";
import { sendPasswordResetEmail } from "firebase/auth";
import { useState } from 'react';
import './loginreg.css'

function ForgotPassword({onLogin}){
    const [email, setEmail] = useState(""); 
    async function resetPassword(e){ 
        e.preventDefault();
        try {
            await sendPasswordResetEmail(auth, email);
            alert("Email Sent!"); 
        } catch (emailError) { 
            alert(emailError.message);
        }
    };
    function setTheEmail(e){
        setEmail(e.target.value);
    };
    return (
        <div className='pageBkg'>
            <form onSubmit={resetPassword} className='inputBlock'>
                <p className='title'>Forgot Password</p>
                <input
                    className='emailInput'
                    type="email"
                    value={email}
                    onChange={setTheEmail}
                    placeholder="Enter Email"
                />
                <button className='userButton'type="submit">Submit</button>
                <div className='butContainer'>
                    <p className='regLink'>Return to login   <button className='clickLink' onClick={onLogin}>click here</button></p>
                </div>
            </form>
        </div>
    );
}
    
export default ForgotPassword;