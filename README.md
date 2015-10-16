# Data Science with Move Loot

 My Insight Data Science project was a partnership with [Move Loot](https://www.moveloot.com/sf), a local startup that provides an online platform to buy and sell used furniture. I was excited about working with Move Loot for a number of reasons. First, their mission is to promote sustainability by prolonging the life of pieces of furniture, and sustainability is a value I hold dear. Second, Move Loot’s data was complex in space and time, which led to many interesting data science questions that, when solved, would provide immense direct benefits to the business. Third, it provided me an opportunity to learn data mapping techniques (I love maps!).

## Prediction model

Move Loot's business is thriving, and they have expanded from the San Francisco bay area to 6 other cities in the country since being founded in 2013. Their current business need is to better understand and be able to predict customer demand. To do this, Move Loot must know both **where** their customers are and **when** they want to buy or sell furniture.

Move Loot gave me data for most of their bay area furniture deliveries and pickups since the start of 2015. The first thing I did was to map the spatial characteristics of their customer demand. It should surprise no one that the most active neighborhoods were all in San Francisco.

<img src="https://raw.githubusercontent.com/tesskbot/moveloot_public/master/images/driveregions.png" width="600">

Historical business volumes were then used to predict future business volumes.

### A note on nomenclature

For future reference, customers buying furniture are classified by Move Loot as deliveries, since Move Loot delivers furniture to those customers, while customers selling furniture are classified by Move Loot as pickups, since Move Loot picks up furniture from those customers.

### Model building

People selling furniture have different motivations than those buying furniture. That may sound obvious, but it means that I needed separate predictive models for buyers and sellers. For Move Loot to have maxiumum flexibility in their predictions, I created three models: one that predicts deliveries (customers buying), one that predicts pickups (customers selling), and one that predicts the sum of pickups and deliveries. Move Loot can use the number of total pickups and deliveries to determine, in aggregate, how many times they will visit a particular area, regardless of whether furniture goes into the truck or out of it.

### Defining a feature space

I knew from exploratory analysis that the number of pickups and deliveries was heavily dependent on the day of the week, and I expected that other temporal features were important, too. I engineered a set of 60 features that could predict demand for buying and selling used furniture. The set of features included the day of the week, the day of the month, the week of the month, whether it was a weekend or a holiday weekend, et cetera, and many combinations of the above.

For each of my three cases (pickups only, deliveries only, pickups and deliveries), I trained lasso regression models that considered all 60 features. Lasso models are linear models that penalize the size of the regression coefficients. The lasso makes the coefficient of unimportant features drop to zero so that only features that contribute to creating a good fit have any sway on the model output.

Each model was trained on 7 months worth of spatially-aggregated data, from January to July 2015. Each of the three models had its own set of important features, as determined by the lasso regression. All of them heavily considered the day of the week, as, in general, people preferred to have furniture picked up and delivered on Friday, Saturday, and Sunday. Further, people tended to sell more furniture at the end of the month than the beginning, so the week of the month was an important feature in the pickups model. Many of the combined features were also important, such as whether it was a weekend **and** the last week of the month.  

### Dynamic model creation

Move Loot needed prediction models that could be applied at all levels of spatial granularity. This meant that the models must be **fast and flexible**. For example, if Move Loot wants to know how many pickups they will have to make in San Francisco's marina district next Monday, a linear regression model will be trained using only the features previously determined to be important for pickups, where the dependent variable (y) is the historical number of pickups in the marina district.

Predictions of the pickup, delivery, or pickup and delivery volume can then be generated for any individual region or group of regions. These predictions are flexible, fast, easy to understand, and allow Move Loot to plan better for the future.

*Techinical note:* by first using lasso regression to select features and **then** using those features to predict demand in restricted spatial domains, I am making the assumption that the motivations behind demand for furniture pickups/deliveries are the same in every spatial region. This is not necessarily true. However, given my restricted dataset, it was not possible to use lasso regression to predict events in areas with very low event frequency. So, I erred on the side of enforcing periodicity rather than not capturing any periodicity at all. Future iterations of the model could better take spatial differences into account.

### Dashboard

I built a Dashboard that allows Move Loot to visualize and interact with their historical data, as well as generate predictions for future pickup and delivery volumes in any given area. Here are a couple of screenshots of that dashboard.

<img src="https://raw.githubusercontent.com/tesskbot/moveloot_public/master/images/historical_data.png" width="300"><img src="https://raw.githubusercontent.com/tesskbot/moveloot_public/master/images/prediction.png" width="300">

## Clustering analysis

Even though most of their customers are in San Francisco, Move Loot picks up and delivers furniture throughout the greater Bay Area. However, traveling costs money: Move Loot pays for truck driver salaries, truck maintenance, gas, and bridge tolls. In order to estimate travel costs from their Oakland warehouse to each zip code in the Move Loot bay area region, I queried the Google Maps API to get travel distance and travel time. I then calculated travel cost to each zip code. This travel cost is only a rough scaling factor since each time the truck travels it makes multiple stops along the way and the cost of gas varies with time and place.

The drive cost may be an estimate, but it also represents a direct link to Move Loot’s operating costs. I used drive cost values, latitude, and longitude as inputs into a k-means clustering algorithm. The output of k-means, after a bit of manual clean up (a luxury in this instance where there are only around 200 different zip codes), is their bay area market separated into functionally relevant regions:

<img src="https://raw.githubusercontent.com/tesskbot/moveloot_public/master/images/clustered_regions.png" width="600">

Domain knowledge of the bay area serves as validation that this clustered map represents logical and useful divisions of the bay area. One clear area where the clustering algorithm is not optimized is in the yellow region above: it covers both San Francisco and Richmond, which are separated by the bay. This is a reminder that even powerful data science techniques benefit from expert eyes.

Important insights can be made from this clustering analysis. For example, here is a graph representing the average travel cost in each region versus the number of visits per week (expressed as a percentage).

<img src="https://raw.githubusercontent.com/tesskbot/moveloot_public/master/images/cluster_graph.png" width="600">

It’s cheap for Move Loot to drive to regions in the inner East bay, near the warehouse. It’s a bit more expensive to drive to San Francisco, but there are so many pickups and deliveries there that this cost is quickly recouped. However, in the South bay, for example, it costs a lot of money to drive there AND there isn’t as much demand. In order to make the trip worth the hefty price tag, Move Loot needs to buy and sell as many things as possible in each trip.

## Toolkit

I used python's pandas package for data cleaning and processing, scikit learn for k-means clustering and model creation, folium for mapping, and flask and bootstrap to create the dashboard. All the code I wrote for this project was delivered to Move Loot, and a subset of that code is [on github](https://github.com/tesskbot/moveloot_public). The slides I created to present this project [are here](https://tesskbot.github.io/slides). I loved the opportunity to learn a ton of new things while working on this project, and hope to write future posts describing the more technical details of those tools. 

## Summary

The outputs of the prediction models combined with the intelligent regional clustering will allow Move Loot to make more data-driven business decisions. They can better schedule truck drivers and warehouse staff to match demand, create delivery and pricing schemes that will optimize their resources, decide where to create new warehouses, and plan expansions into new cities.

It was a lot of fun working with Move Loot! It was great to build prediction models that work well even on sparse and stochastic data, and I loved to opportunity to hone my existing data science skills and learn new tools. The most rewarding part was providing a valuable service to a company that I believe in.
