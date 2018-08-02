import private

## import private variables

# Slack token

SLACK_TOKEN = private.SLACK_TOKEN

# Google API key

GMAPS_KEY = private.GMAPS_KEY

# DB connection info

DB_NAME = private.DB_NAME

DB_USER = private.DB_USER

DB_PASSWORD = private.DB_PASSWORD

## Other settings

# maximum price you want to pay

MAX_PRICE = '2000000'

# name of slack channel

SLACK_CHANNEL = "#housing"

# how long we want to wait between scraping cycles

SLEEP_INTERVAL = 20 * 60  # 20 minutes

# agencies settings

AGENCIES = {
    'SREALITY': {
        "url": 'https://www.sreality.cz',
        "browserLink": 'https://www.sreality.cz/hledani/prodej/pozemky/stavebni-parcely/stredocesky-kraj,praha?cena-od=0&cena-do=' + MAX_PRICE,
        "linkRegexp": '(/detail/prodej/pozemek/.+?)"',
        "nextPageRegexp": 'paging-next" ng-class="{disabled: !pagingData.nextUrl}" href="(.+?)"></a>',
        "locationRegexp": '<span class="location-text ng-binding">(.+?)</span>',
        "priceRegexp": 'itemprop="price" class="ng-binding">(.+?)<',
        "sizeRegexp": 'plocha-pozemku&quot;:&quot;(\d.+?)&quot'

    },
    'BEZREALITKY': {
        "url": 'https://www.bezrealitky.cz',
        "browserLink": 'https://www.bezrealitky.cz/vypis/nabidka-prodej/pozemek/stredocesky-kraj?priceTo=' + MAX_PRICE + '&',
        "linkRegexp": '<a href="(.+?)" class="product__link',
        "nextPageRegexp": '<link rel="next" href=(.+?)"',
        "locationRegexp": 'data-fancybox-description="">\n +(.+?)\n',
        "priceRegexp": 'data-fancybox-price="">\n +(.+?)\n',
        "sizeRegexp": 'Plocha:</th>\n +<td colspan="2">\n +(.+?)\n'
    },
    'IDNES': {
        "url": 'https://www.reality.idnes.cz',
        "browserLink": 'https://reality.idnes.cz/s/prodej/pozemky/stavebni-parcela/cena-do-' + MAX_PRICE + '/stredocesky-kraj/',
        "linkRegexp": '(/detail/prodej/pozemek/.+?/.+?/)',
        "nextPageRegexp": '"(.+?)" class="btn paging__next">\n[\t]+<span class="btn__text">\n[\t]+Další',
        "locationRegexp": 'b-detail__info">\n[\t]+(.+?)\n',
        "priceRegexp": 'b-detail__price">\n[\t]+<strong>(.+?)</',
        "sizeRegexp": 'Plocha pozemku</dt>\n[\t]+<dd>(.+?)<'
    }

}


