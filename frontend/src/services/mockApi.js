const MOCK_TABLE_ROWS = [
  { Product: "Aurora Desk Lamp", Category: "Home", Region: "West", Revenue: 48210, Profit: 12500 },
  { Product: "Comet Backpack", Category: "Outdoor", Region: "East", Revenue: 39875, Profit: 9800 },
  { Product: "Nimbus Headphones", Category: "Electronics", Region: "North", Revenue: 35660, Profit: 11020 },
  { Product: "Solstice Water Bottle", Category: "Outdoor", Region: "South", Revenue: 21230, Profit: 6100 },
  { Product: "Lumen Desk Chair", Category: "Home", Region: "West", Revenue: 18590, Profit: 4200 },
];

const MOCK_TREND_CHART = {
  type: "line",
  x_label: "Month",
  y_label: "Revenue",
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
  values: [18200, 21430, 19870, 24310, 27650, 30120],
};

const MOCK_CATEGORY_CHART = {
  type: "bar",
  x_label: "Category",
  y_label: "Revenue",
  labels: ["Home", "Outdoor", "Electronics", "Apparel"],
  values: [66800, 61105, 35660, 22940],
};

function buildMockUploadInfo(fileName) {
  return {
    name: fileName,
    rows: 1284,
    columns: ["Product", "Category", "Region", "Revenue", "Profit", "Date"],
    suggestions: [
      "Top 5 products by revenue",
      "Show revenue trend",
      "Distribution by category",
      "What's the average profit margin?",
    ],
    summary:
      "This dataset contains sales transactions across products, regions, and time. It includes revenue, profit, and category fields suitable for trend and distribution analysis.",
  };
}

function generateMockResponse(query) {
  const q = query.toLowerCase();

  if (q.includes("explain") || q.includes("what") || q.includes("why")) {
    return {
      type: "ai",
      title: "About this dataset",
      insight:
        "The dataset spans six months of transactions across four product categories. Home and Outdoor categories drive the largest share of revenue, while Electronics carries the highest profit margin per unit.",
    };
  }

  if (
    q.includes("average") ||
    q.includes("total") ||
    q.includes("margin") ||
    q.includes("count")
  ) {
    return {
      type: "kpi",
      title: "Average Profit Margin",
      value: 27.4,
      insight:
        "Profit margin has improved 3.1 points versus the prior period, led by the Electronics category.",
    };
  }

  if (q.includes("trend") || q.includes("over time")) {
    return {
      type: "structured",
      title: "Revenue Trend",
      insight:
        "Revenue has grown steadily each month, with the strongest gains in May and June.",
      table: MOCK_TABLE_ROWS.slice(0, 3),
      chart: MOCK_TREND_CHART,
    };
  }

  if (q.includes("distribution") || q.includes("category")) {
    return {
      type: "structured",
      title: "Distribution by Category",
      insight:
        "Home and Outdoor together account for over 60% of total revenue.",
      table: MOCK_TABLE_ROWS,
      chart: MOCK_CATEGORY_CHART,
    };
  }

  return {
    type: "structured",
    title: "Top Results",
    insight:
      "Aurora Desk Lamp leads in both revenue and profit, followed closely by Comet Backpack.",
    table: MOCK_TABLE_ROWS,
    chart: MOCK_CATEGORY_CHART,
  };
}

export {
  buildMockUploadInfo,
  generateMockResponse,
};