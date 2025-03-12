WITH sales_calculation AS (
  SELECT 
    t.transaction_id,
    t.product_id,
    t.quantity,
    p.product_name,
    p.retail_price,
    p.product_class_id,
    pc.product_class_name,
    (t.quantity * p.retail_price) AS sales_value
  FROM 
    `Sales_Transaction` t
  JOIN 
    `Product` p ON t.product_id = p.product_id
  JOIN 
    `Product_Class` pc ON p.product_class_id = pc.product_class_id
),

product_sales AS (
  SELECT 
    product_id,
    product_name,
    product_class_id,
    product_class_name,
    SUM(sales_value) AS total_sales,
    SUM(quantity) AS total_quantity
  FROM 
    sales_calculation
  GROUP BY 
    product_id, product_name, product_class_id, product_class_name
),

ranked_sales AS (
  SELECT 
    product_class_name,
    product_name,
    total_sales AS sales_value,
    ROW_NUMBER() OVER (
      PARTITION BY product_class_id 
      ORDER BY total_sales DESC, total_quantity ASC
    ) AS rank
  FROM 
    product_sales
)

SELECT 
  product_class_name,
  rank,
  product_name,
  sales_value
FROM 
  ranked_sales
WHERE 
  rank <= 2
ORDER BY 
  product_class_name,
  rank;