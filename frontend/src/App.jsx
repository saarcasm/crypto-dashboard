import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [prices, setPrices] = useState({
    bitcoin: { usd: 0 },
    ethereum: { usd: 0 },
    solana: { usd: 0 },
    dogecoin: { usd: 0 }
  })
  
  const [status, setStatus] = useState("Connecting...")

  useEffect(() => {
    // ⚠️ IMPORTANT: Replace this with YOUR Render URL
    // MUST start with wss:// and end with /ws
    const socket = new WebSocket("wss://crypto-dashboard-971r.onrender.com/ws");

    socket.onopen = () => {
      setStatus("Connected ✅");
      console.log("WebSocket Connected");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Data received:", data); // Check console if you see this!
        
        // Update state only if data is valid
        if (data && data.bitcoin) {
           setPrices(data);
        }
      } catch (error) {
        console.error("Error parsing data:", error);
      }
    };

    socket.onclose = () => {
      setStatus("Disconnected ❌ (Reconnecting...)");
      console.log("WebSocket Closed");
    };

    // Cleanup: This closes the connection only when you leave the page
    return () => {
      socket.close();
    };
  }, []); // <--- The empty array [] stops the infinite loop!

  return (
    <div className="dashboard">
      <h1>Crypto Live Tracker</h1>
      <div className="status-bar">Status: {status}</div>
      
      <div className="card-container">
        {/* Bitcoin Card */}
        <div className="card btc">
          <h2>Bitcoin (BTC)</h2>
          <p className="price">${prices.bitcoin.usd.toLocaleString()}</p>
        </div>

        {/* Ethereum Card */}
        <div className="card eth">
          <h2>Ethereum (ETH)</h2>
          <p className="price">${prices.ethereum.usd.toLocaleString()}</p>
        </div>

        {/* Solana Card */}
        <div className="card sol">
          <h2>Solana (SOL)</h2>
          <p className="price">${prices.solana.usd.toLocaleString()}</p>
        </div>

        {/* Dogecoin Card */}
        <div className="card doge">
          <h2>Dogecoin (DOGE)</h2>
          <p className="price">${prices.dogecoin.usd}</p>
        </div>
      </div>
    </div>
  )
}

export default App