# Shop-Tool for viewing and creating orders for WooCommerce
As a feature one can create custom items and custom discounts for each order

## Configuration

To run the application, you need to set up your WooCommerce API credentials.

1.  Copy the configuration template:
    ```bash
    cp config.json.template config.json
    ```
2.  Open `config.json` in a text editor.
3.  Fill in your specific `woo_url`, `consumer_key`, and `consumer_secret`.
4.  Save the `config.json` file. This file is ignored by Git, so your credentials will remain local.

The application will load these settings when it starts. If `config.json` is missing or if there's an error loading it, default empty values will be used, and the API connection will likely fail until configured.
