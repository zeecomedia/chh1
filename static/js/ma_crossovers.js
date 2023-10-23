/*
* Creates the function that generates the Short and Long moving average model
* */

function generateChart(event) {
    if (event) event.preventDefault();

    // Gather form data
    const formData = new FormData(document.querySelector('#generate-chart-form'));
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const transaction_costs = document.getElementById('transaction_costs').value;

    formData.append('start_date', startDate);
    formData.append('end_date', endDate);
    formData.append('transaction_costs', Math.round(parseFloat(transaction_costs)));

    // Update the browser's URL to reflect the current form data
    window.history.pushState({}, "", "?" + new URLSearchParams(formData).toString());

    // Make an AJAX request to the server
    fetch('/generate_chart', {
        method: 'POST',
        body: formData,
    })

            .then(response => response.json())
            .then(data => {
                console.log(data)
                if (data.status === 'error') {
                    // Show the error message in a popup
                    alert(data.message);
                } else {
                    // Update the session data
                    sessionStorage.setItem('symbol', data.symbol);
                    sessionStorage.setItem('short', data.short);
                    sessionStorage.setItem('long', data.long);
                    sessionStorage.setItem('ind', data.ind);
                    sessionStorage.setItem('start_date', data.start_date);
                    sessionStorage.setItem('end_date', data.end_date);
                    sessionStorage.setItem('transaction_costs', data.transaction_costs);


                    // Update the table and chart
                    document.querySelector('#table-container').innerHTML = data.table_html;
                    console.log(data.table_html)

// Use the received chart_data
                    const chart_data = JSON.parse(data.chart_data);

                    const stockdata = chart_data.data.map(row => [row[1], row[6]]);
                    const longMAdata = chart_data.data.map(row => [row[1], row[9] !== null ? row[9] : row[11]]);
                    const shortMAdata = chart_data.data.map(row => [row[1], row[8] !== null ? row[8] : row[10]]);
                    const buysData = chart_data.data.map((row, index) => row[16] ? [row[1], row[6]] : null).filter(x => x !== null);
                    const sellsData = chart_data.data.map((row, index) => row[17] ? [row[1], row[6]] : null).filter(x => x !== null);
                    const indexedStockReturnData = chart_data.data.map(row => [row[1], row[14]]);
                    const normalisedStockReturnData = chart_data.data.map(row => [row[1], row[15]]);

                    console.log('buysData', buysData);
                    console.log('sellsData', sellsData);


                    console.log(stockdata)
                    console.log(longMAdata)
                    console.log(shortMAdata)

                    // Create a Highcharts chart using the loaded data
                    Highcharts.chart('chart-container', {
                        chart: {
                            type: 'line'
                        },
                        title: {
                            text: 'Stock chart'
                        },
                        xAxis: {
                            type: 'datetime',
                        },

                        series: [{
                            name: 'Stock price',
                            data: stockdata,
                            zIndex: 1,
                            marker: {
                                enabled: false
                            }
                        }, {
                            name: 'Short moving average',
                            data: shortMAdata,
                            zIndex: 1,
                            marker: {
                                enabled: false
                            }
                        }, {
                            name: 'Buy',
                            data: buysData,
                            type: 'scatter',
                            marker: {
                                symbol: 'triangle',
                                fillColor: 'green',
                                radius: 5,
                            },
                            tooltip: {
                                pointFormat: 'Buy: {point.y}'
                            }
                        },
                            {
                                name: 'Sell',
                                data: sellsData,
                                type: 'scatter',
                                marker: {
                                    symbol: 'triangle-down',
                                    fillColor: 'red',
                                    radius: 5,
                                },
                                tooltip: {
                                    pointFormat: 'Sell: {point.y}'
                                }
                            }, {
                                name: 'Long moving average',
                                data: longMAdata,
                                zIndex: 1,
                                marker: {
                                    enabled: false
                                }
                            },

                        ],
                        navigator: {
                            enabled: true
                        },
                        rangeSelector: {
                            enabled: true,
                            buttons: [{
                                type: 'month',
                                count: 1,
                                text: '1M'
                            }, {
                                type: 'month',
                                count: 3,
                                text: '3M'
                            }, {
                                type: 'month',
                                count: 6,
                                text: '6M'
                            }, {
                                type: 'ytd',
                                text: 'YTD'
                            }, {
                                type: 'year',
                                count: 1,
                                text: '1Y'
                            }, {
                                type: 'all',
                                text: 'All'
                            }],
                            selected: 5
                        }
                    });
                    Highcharts.chart('chart-container-2', {
                        chart: {
                            type: 'line'
                        },
                        title: {
                            text: 'Strategy Return'
                        },
                        xAxis: {
                            type: 'datetime',
                        },
                        series: [{
                            name: 'Stock Return',
                            data: normalisedStockReturnData,
                            zIndex: 1,
                            marker: {
                                enabled: false
                            }
                        }, {
                            name: 'Strategy Return',
                            data: indexedStockReturnData,
                            zIndex: 1,
                            marker: {
                                enabled: false
                            }
                        },],
                        navigator: {
                            enabled: true
                        },
                        rangeSelector: {
                            enabled: true,
                            buttons: [{
                                type: 'month',
                                count: 1,
                                text: '1M'
                            }, {
                                type: 'month',
                                count: 3,
                                text: '3M'
                            }, {
                                type: 'month',
                                count: 6,
                                text: '6M'
                            }, {
                                type: 'ytd',
                                text: 'YTD'
                            }, {
                                type: 'year',
                                count: 1,
                                text: '1Y'
                            }, {
                                type: 'all',
                                text: 'All'
                            }],
                            selected: 5
                        }
                    });
                }
            });


}

//listen for DOM content loaded to check if the URL contains the required parameters
document.addEventListener("DOMContentLoaded", function() {
    const params = new URLSearchParams(window.location.search);

    if (params.has("start_date") && params.has("end_date")) {
        // Populate form fields from URL
        document.getElementById('start_date').value = params.get("start_date");
        document.getElementById('end_date').value = params.get("end_date");
        document.getElementById('symbol').value = params.get("symbol");
        document.getElementById('short').value = params.get("short");
        document.getElementById('long').value = params.get("long");
        document.getElementById('ind').value = params.get("ind");
        document.getElementById('transaction_costs').value = params.get("transaction_costs");

        // Save to sessionStorage
        sessionStorage.setItem('symbol', params.get("symbol"));
        sessionStorage.setItem('short', params.get("short"));
        sessionStorage.setItem('long', params.get("long"));
        sessionStorage.setItem('ind', params.get("ind"));
        sessionStorage.setItem('start_date', params.get("start_date"));
        sessionStorage.setItem('end_date', params.get("end_date"));
        sessionStorage.setItem('transaction_costs', params.get("transaction_costs"));
    }
});

document.querySelector('#generate-chart-form').addEventListener('submit', generateChart);

document.addEventListener("DOMContentLoaded", function() {
  // Click the button here
    document.getElementById("generate-chart-button").click();
});