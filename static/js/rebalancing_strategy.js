
let requestData;

function getReturnData() {
    const stock1 = document.getElementById('stock1').value;
    const stock2 = document.getElementById('stock2').value;
    const weight1 = document.getElementById('weight1').value;
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const rebalancing_period = document.getElementById('rebalancing_period').value;

    requestData = {
        stock1: stock1,
        stock2: stock2,
        rebalancing_period:rebalancing_period,
        weight1: weight1,
        start_date: startDate,
        end_date: endDate
    };

    fetch('/get_return_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
        .then(response => response.text())
        .then(html => {
            console.log("HTML response:", html);
            document.getElementById("table-container").innerHTML = html;
        })
        .catch(error => console.error(error));
}


function app() {
    return {
        stock1: 'QQQ',
        stock2: 'BIL',
        weight1: 0.7,
        rebalancing_period: 30,
        start_date: '2000-01-01',
        end_date: '2023-04-01',
        chart: null,
        showStock1: true,
        showPortfolio: true,

        submitRebalancingForm() {
            console.log('Submitting form...');
            const requestData = {
                stock1: this.stock1,
                stock2: this.stock2,
                weight1: this.weight1,
                start_date: this.start_date,
                end_date: this.end_date,
                rebalancing_period: this.rebalancing_period,
            };

            // Fetch CSV data from the Flask app
            fetch('/get_rebalancing_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((jsonData) => {
                    this.renderChart(jsonData);
                })
                .catch((error) => {
                    console.error('Error fetching data:', error);
                });
        },
        renderChart(jsonData) {
            // Parse JSON data
            const data = JSON.parse(jsonData);
            const portfolioValueData = data.data.map(row => [new Date(row[0]).getTime(), row[1]]);
            const stock1Data = data.data.map(row => [new Date(row[0]).getTime(), row[5]]);


            if (!this.chart) {
                this.chart = Highcharts.chart('chart-container', {
                    chart: {
                        type: 'line',
                    },
                    title: {
                        text: 'Stock Rebalancing Strategy',
                    },
                    xAxis: {
                        type: 'datetime',
                    },
                    yAxis: {
                        title: {
                            text: 'Price',
                        },
                    },
                    series: [
                        {
                            name: 'Portfolio Value',
                            data: portfolioValueData,
                        },
                        {
                            name: this.stock1,
                            data: stock1Data,
                        },
                    ],
                    rangeSelector: {
                        enabled: true,

                        buttons: [
                            {
                                type: 'month',
                                count: 1,
                                text: '1m',
                            },
                            {
                                type: 'month',
                                count: 3,
                                text: '3m',
                            },
                            {
                                type: 'month',
                                count: 6,
                                text: '6m',
                            },
                            {
                                type: 'ytd',
                                text: 'YTD',
                            },
                            {
                                type: 'year',
                                count: 1,
                                text: '1y',
                            },
                            {
                                type: 'all',
                                text: 'All',
                            },
                        ],
                        selected: 5,
                    },
                    navigator: {
                        enabled: true
                    }
                });
            } else {
                const series = [];
                if (this.showPortfolio) {
                    series.push({
                        name: 'Portfolio Value',
                        data: portfolioValueData,
                    });
                }
                if (this.showStock1) {
                    series.push({
                        name: 'Stock 1',
                        data: stock1Data,
                    });
                }

                this.chart.update({
                    series: series,
                });
            }

        },


    }
}

document.addEventListener("DOMContentLoaded", function() {
  // Click the button here
  document.getElementById("rebalancing-button").click();
});
