import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, AreaSeries } from 'lightweight-charts';

function App() {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const seriesRef = useRef();
  
  // Cache for history
  const coinDataRef = useRef({
    'BTC/USDT': [], 'ETH/USDT': [], 'SOL/USDT': [], 'BNB/USDT': [], 'DOGE/USDT': []
  });

  const [activeCoin, setActiveCoin] = useState('BTC/USDT');
  const [price, setPrice] = useState(0);
  const [isAutoScaled, setIsAutoScaled] = useState(true); // Track if we are in auto-mode
  
  const coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT'];

  useEffect(() => {
    // 1. Initialize Chart with ADVANCED INTERACTION
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      
      // ENABLE ZOOMING & PANNING
      handleScale: {
        axisPressedMouseMove: true, // Allow dragging the axis
        mouseWheel: true,           // Allow scrolling
        pinch: true,                // Allow trackpad pinch
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        vertTouchDrag: true,
      },
      
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
        borderColor: '#1f2937',
      },
      // Allow the Price Axis to be manually scaled
      rightPriceScale: {
        borderColor: '#1f2937',
        autoScale: true, 
      },
    });

    const newSeries = chart.addSeries(AreaSeries, {
      lineColor: '#2962FF',
      topColor: 'rgba(41, 98, 255, 0.5)',
      bottomColor: 'rgba(41, 98, 255, 0.0)',
      lineWidth: 2,
    });

    chartRef.current = chart;
    seriesRef.current = newSeries;

    // Detect when user manually zooms (disables auto-scale)
    chart.timeScale().subscribeVisibleTimeRangeChange(() => {
       // We could track user interaction here if needed
    });

    // Restore Data
    if (coinDataRef.current[activeCoin].length > 0) {
       newSeries.setData(coinDataRef.current[activeCoin]);
       const lastData = coinDataRef.current[activeCoin][coinDataRef.current[activeCoin].length - 1];
       setPrice(lastData.value);
    }

    const handleResize = () => {
      chart.applyOptions({ 
        width: chartContainerRef.current.clientWidth,
        height: chartContainerRef.current.clientHeight
      });
    };
    window.addEventListener('resize', handleResize);

    const ws = new WebSocket('wss://crypto-dashboard-971r.onrender.com/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const formattedData = {
          time: data.timestamp / 1000,
          value: data.price,
      };

      if (coinDataRef.current[data.symbol]) {
        if (coinDataRef.current[data.symbol].length > 2000) {
            coinDataRef.current[data.symbol].shift();
        }
        coinDataRef.current[data.symbol].push(formattedData);
      }
      
      if (data.symbol === activeCoin) {
        setPrice(data.price);
        seriesRef.current.update(formattedData);
      }
    };

    return () => {
      ws.close();
      chart.remove();
      window.removeEventListener('resize', handleResize);
    };
  }, [activeCoin]);

  const handleCoinSwitch = (coin) => {
    setActiveCoin(coin);
    setIsAutoScaled(true); // Reset to auto-scale on switch
  };

  // BUTTON FUNCTION: Re-enable Auto-Scaling
  const handleResetZoom = () => {
      chartRef.current.timeScale().fitContent();
      chartRef.current.priceScale('right').applyOptions({
          autoScale: true
      });
      setIsAutoScaled(true);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: '#0d1117', color: 'white' }}>
      
      {/* SIDEBAR */}
      <div style={{ 
        width: '250px', borderRight: '1px solid #1f2937', padding: '20px',
        display: 'flex', flexDirection: 'column', gap: '10px'
      }}>
        <h2 style={{ color: '#2962FF', margin: '0 0 20px 0' }}>⚡ TradeDeck</h2>
        {coins.map((coin) => (
          <button
            key={coin}
            onClick={() => handleCoinSwitch(coin)}
            style={{
              padding: '12px', textAlign: 'left',
              background: activeCoin === coin ? '#1f2937' : 'transparent',
              border: activeCoin === coin ? '1px solid #2962FF' : '1px solid transparent',
              color: 'white', borderRadius: '8px', cursor: 'pointer',
              fontWeight: 'bold', transition: 'all 0.2s'
            }}
          >
            {coin}
          </button>
        ))}
      </div>

      {/* MAIN CHART */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        
        {/* Header Overlay */}
        <div style={{ 
          position: 'absolute', top: 20, left: 20, zIndex: 10,
          background: 'rgba(13, 17, 23, 0.8)', padding: '10px 20px',
          borderRadius: '12px', backdropFilter: 'blur(5px)', border: '1px solid #1f2937'
        }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>{activeCoin}</h1>
          <h2 style={{ margin: 0, fontSize: '32px', color: '#2962FF' }}>
            ${price.toLocaleString()}
          </h2>
        </div>

        {/* RESET ZOOM BUTTON */}
        <button 
            onClick={handleResetZoom}
            style={{
                position: 'absolute', top: 20, right: 60, zIndex: 10,
                background: '#1f2937', color: 'white', border: '1px solid #374151',
                padding: '8px 16px', borderRadius: '6px', cursor: 'pointer'
            }}
        >
            Reset View
        </button>

        <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  );
}

export default App;