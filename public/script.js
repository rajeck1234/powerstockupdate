const API = "https://powerstockupdate-production.up.railway.app/";
//const API = "http://localhost:3000";

// const API = "https://stockmarket-production-8cf0.up.railway.app/"
// const API = "https://stockmarket-8e8r.onrender.com";
coun =0
const alarm = new Audio("alarm.mp3");
let alertStocks = [];

// Load stocks

coun1 = 0
coun2 =0
async function loadStocks() {


    coun++
    const res = await fetch(API + "/stocks");
    const data = await res.json();
    // console.log(coun); 
    const div = document.getElementById("stocks");
    div.innerHTML = "";

    data.forEach(stock => {
        
        div.innerHTML += `
        <div class="stock">
            <h3>${coun}</h3>
            <h3>${stock.name}</h3>
            <p>Price: ₹${stock.price}</p>
            <button onclick="buyStock('${stock.name}')">

                Buy
            </button>
            <button onclick="removeStock('${stock.name}')">
             Remove
             </button>
        </div>
        `;
    });
}

// Portfolio

async function checkAlerts() {
    console.log("check1");
    const res = await fetch(API + "/check-alerts");
    const data = await res.json();
    alertStocks = data;
    loadPortfolio();

    // console.log("check1");
    // console.log(data);

    if (data.length > 0) {
        alarm.play();
        document.getElementById("stopAlarm").style.display = "block";
    }
}
async function addStock() {

    let symbol = prompt("Enter Stock Symbol (Example: HCLTECH)");

    if (!symbol) return;

    await fetch(API + "/add-stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol })
    });

    loadStocks();
}
async function removeStock(name){

    await fetch(API + "/removeStock/" + name,{
        method:"DELETE"
    });

    loadStocks();
}

async function loadPortfolio() {

    const res = await fetch(API + "/portfolio");
    const data = await res.json();

    const div = document.getElementById("portfolio");
    div.innerHTML = "";

    data.forEach(stock => {
        const isAlert = alertStocks.includes(stock.name);
        console.log("Alert Stocks:", alertStocks);
        console.log("Current Stock:", stock.name);
        div.innerHTML += `
        <div class="stock ${isAlert ? "alert-stock" : ""}">

            <h3>${stock.name}</h3>
            <p>Bought At: ₹${stock.buy_price}</p>
            <button 
    onclick="sellStock('${stock.name}')"
    class="${isAlert ? "sell-alert" : ""}">
                Sells
            </button>
        </div>
        `;
    });
}

// Buy

async function buyStock(name) {

    let price = prompt("Enter your purchase price");

    if (!price) return;

    await fetch(API + "/buy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, price })
    });

    loadPortfolio();
}

// async function buyStock(name, price) {
//     await fetch(API + "/buy", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ name, price })
//     });

//     loadPortfolio();
// }

// Sell
function stopAlarm() {
    alarm.pause();
    alarm.currentTime = 0;
    document.getElementById("stopAlarm").style.display = "none";
}

async function sellStock(name) {
    await fetch(API + "/sell", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
    });

    loadPortfolio();
}

async function loadMomentum30() {

    const res = await fetch("/momentum30");
    const data = await res.json();
    coun++
    const container = document.getElementById("momentum30");
    container.innerHTML = "";

    data.forEach(stock => {

        const div = document.createElement("div");
        div.className = "stock";

        div.innerHTML = `
            <div style="flex:1; font-weight:bold;">
                ${coun1}&nbsp;
                ${stock.name}
                &nbsp;&nbsp;
                ₹${stock.price.toFixed(2)}
                &nbsp;
                (${stock.change.toFixed(2)}%)

            </div>

            <button class="buy" onclick="buyStock('${stock.name}', ${stock.price})">
                Buy
            </button>
        `;

        container.appendChild(div);
    });
}



async function loadMomentum3() {

    const res = await fetch("/momentum3min");
    const data = await res.json();

    const container = document.getElementById("momentum3");
    container.innerHTML = "";
    coun2++
    data.forEach(stock => {

        const div = document.createElement("div");
        div.className = "stock";

        div.innerHTML = `
            <div style="flex:1; font-weight:bold;">
                ${stock.name}
                &nbsp;&nbsp;
                ₹${stock.price.toFixed(2)}
                &nbsp;
                (${stock.change.toFixed(2)}%)
            </div>

            <button class="buy" onclick="buyStock('${stock.name}', ${stock.price})">
                Buy
            </button>
        `;

        container.appendChild(div);
    });
}



// setInterval(loadMomentum30,30000);
// setInterval(loadMomentum3,180000);

setInterval(loadMomentum30,5000);
setInterval(loadMomentum3,5000);

// Auto refresh stocks every 5 sec
setInterval(loadStocks, 5000);
setInterval(checkAlerts, 5000);

loadMomentum30();
loadMomentum3();
loadStocks();
loadPortfolio();
