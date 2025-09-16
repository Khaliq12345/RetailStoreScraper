update_headers = {
    "Host": "ocscd.prd.sbs.orckestra.cloud",
    "X-Auth": "OFG2WVNLNMnL54IOkP6lgg0VjH/rOrszabElgBIvK3QPgl6o1v8Z7WBpG8n+Xf5gm3UM0U0YSiM9/UnmiVH/xPhVYkdNr+T/2sP3lCQ9EJkmbS2kPjF9VdFocoPhJ/ne1AfSDz0lkJlD5cJ1/BkOWN5dxaUW1+qfwBI/uWCms0nKCF174LC25rrpVMpDCPzR3PwnQut839YDIZHDf+1W/g==",
    "Accept": "application/json",
    "Accept-Charset": "UTF-8",
    "User-Agent": "Ktor client",
    "Content-Type": "application/json",
}

update_json_data = {
    "productIds": [
        "",
    ],
    "includePriceLists": True,
    "cultureName": "en-CA",
}

full_headers = {
    "Accept": "application/json",
    "Accept-Charset": "UTF-8",
    # 'Accept-Encoding': 'gzip',
    "Connection": "Keep-Alive",
    "Content-Type": "application/json",
    "Host": "ocscd.prd.sbs.orckestra.cloud",
    "User-Agent": "Ktor client",
    "X-Auth": "w8HV6AbRt84jq3XsN4c8cJDWDZtdzyjCoWKXsUObDMqiO6N712HlIaF4sB9e6Hc9S/KTIuIEm4bF4r3Omlx49M7gATDyn5Yca4dgBkEbi0MjDkJ11/gM/CbeVf1aWrYHpdHrMlwpWVjJe5sDUE62H80gMcsSkaew1L76HjEPSjkT7jCa9fUTZ7NQp25ZPgSunj3cg3UPJrz8l4wDFg2HZw==",
}

full_params = {
    "format": "json",
}

full_json_data = {
    "availabilityDate": "2025-09-16T01:00:00.0000000-0400",
    "cultureName": "en-CA",
    "includeFacets": False,
    "inventoryLocationIds": [
        "10593D1",
    ],
    "inventoryLocationOperator": "Or",
    "properties": [
        "ProductId",
        "Sku",
        "AdditionalInformation",
        "DisplayName",
        "FullDisplayName",
        "ProductImageFile",
        "BrandName",
        "Size",
        "IsWeightedProduct",
        "MadeIn",
        "IsInFlyerCurrentPeriod",
        "IsNewProduct",
        "ProductGlutenFree",
        "IsPopular",
        "ComparisonMeasure",
        "IsInPromotionCurrentPeriod",
        "PromotionDescription",
        "CategoryLevel1DisplayName",
        "CategoryLevel2DisplayName",
        "CategoryLevel3DisplayName",
        "IsNewPrice",
        "CategoryLevel1",
        "CategoryLevel2",
        "CategoryLevel3",
    ],
    "query": {
        "distinctResults": False,
        "hierarchyDepth": 0,
        "includeTotalCount": True,
        "maximumItems": 100,
        "startingIndex": 0,
        "filter": {
            "binaryOperator": "And",
            "filters": [
                {
                    "member": "Active",
                    "value": "True",
                    "not": False,
                    "operator": "Equals",
                },
                {
                    "member": "CatalogId",
                    "value": "IGA",
                    "not": False,
                    "operator": "Equals",
                },
                {
                    "member": "AvailableOnline",
                    "value": "True",
                    "not": False,
                    "operator": "Equals",
                },
                {
                    "member": "CategoryLevel1DisplayName",
                    "value": "Beverages",
                    "not": False,
                    "operator": "Equals",
                },
            ],
        },
        "sortings": [
            {
                "direction": "Descending",
                "propertyName": "score",
            },
        ],
    },
    "scopeId": "IGA",
    "searchTerms": "",
    "filterByPastPurchases": False,
    "boostByPastPurchases": False,
    "removeChildren": False,
    "ignoreSolrConfigDefaultBoost": False,
}
