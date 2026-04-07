import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


st.set_page_config(page_title="Hotel Dashboard", layout="wide")

st.sidebar.title("🏨 Hotel Analytics")
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_hotel_data.csv')
    return df

df = load_data()
#df = pd.read_csv('cleaned_hotel_data.csv')

page = st.sidebar.radio(
    'Pages',
    ['Main Dashboard', 'Analysis', 'Insights and recommendations']
)

st.sidebar.title('Filters')

nationality_filter = st.sidebar.multiselect(
    'Nationality',
    options=df['nationality'].unique(),
    default=df['nationality'].unique()
)

channel_filter = st.sidebar.multiselect(
    'Distribution Channel',
    options=df['distributionchannel'].unique(),
    default=df['distributionchannel'].unique()
)

market_filter = st.sidebar.multiselect(
    'Market Segment',
    options=df['marketsegment'].unique(),
    default=df['marketsegment'].unique()
)




age_filter = st.sidebar.slider(
    'Age Range',
    int(df['age'].min()),
    int(df['age'].max()),
    (int(df['age'].min()), int(df['age'].max()))
)

filtered_df = df[
    (df['nationality'].isin(nationality_filter)) &
    (df['distributionchannel'].isin(channel_filter)) &
    (df['marketsegment'].isin(market_filter)) &
    (df['age'].between(age_filter[0], age_filter[1])) 
]


if page == "Main Dashboard":
    st.title("📊 Main Dashboard")
    st.markdown("---")


    st.subheader("Dataset Preview")
    st.dataframe(filtered_df)


    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🧑‍🤝‍🧑 Total Customers", len(filtered_df))
    col2.metric("💰 Total Revenue", f"${filtered_df['total_revenue'].sum():,.0f}")
    col3.metric("🛏️ Avg Revenue/Night", f"${filtered_df['revenue_per_night'].mean():,.1f}")
    col4.metric(
        "❌ Cancellation Rate",
        f"{filtered_df['bookingscanceled'].sum() / filtered_df['total_bookings'].sum() * 100:.1f}%"
    )

    st.markdown("---")


elif page == "Analysis":

    st.title("📊 Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Booking Overview", "Cancellation Analysis", "Revenue Analysis", "Customer Insights"]
    )


    with tab1:
        st.subheader("Booking Overview")
        col1, col2 = st.columns(2)

        with col1:
            booking_status = pd.DataFrame({
                'status': ['Checked In ✅', 'Canceled ❌', 'No Show 🚫'],
                'count': [
                    filtered_df['bookingscheckedin'].sum(),
                    filtered_df['bookingscanceled'].sum(),
                    filtered_df['bookingsnoshowed'].sum()
                ]
            })

            fig = px.pie(booking_status,values='count',names='status',hole=0.4,
                title='Booking Status Distribution',
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            fig.update_traces(textinfo='percent+value')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            booked_df = filtered_df[filtered_df['bookingscheckedin'] > 0]
            seg = booked_df['marketsegment'].value_counts().reset_index()
            seg.columns = ['marketsegment', 'bookingcount']

            fig = px.bar(seg,x='marketsegment',y='bookingcount',
                title='Market Segment Distribution',
                color='marketsegment',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

        has_booking = filtered_df[(filtered_df['bookingscheckedin'] > 0) |(filtered_df['bookingscanceled'] > 0) |(filtered_df['bookingsnoshowed'] > 0)]
        no_booking = filtered_df[(filtered_df['bookingscheckedin'] == 0) &(filtered_df['bookingscanceled'] == 0) & (filtered_df['bookingsnoshowed'] == 0)]

        booking_summary = pd.DataFrame({
            'status': ['Booking', 'No Booking'],
            'count': [len(has_booking), len(no_booking)]
        })

        fig = px.pie( booking_summary,values='count',names='status',title='Customer Engagement (Booking vs No Booking)',hole=0.4)
        fig.update_traces(textinfo='percent+value')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")



    with tab2:
        st.subheader("Cancellation Analysis")

        #max_val = filtered_df['averageleadtime'].max()
        bins = [0, 30, 60, 90, 180, 365, 100000]
        labels = ['0-30', '31-60', '61-90', '91-180', '181-365', '365+']

        filtered_df['lead_bin'] = pd.cut(
            filtered_df['averageleadtime'],
            bins=bins,
            labels=labels,
            include_lowest=True #(min , max values)
        )
        cancel_trend = filtered_df.groupby('lead_bin')['bookingscanceled'].mean().reset_index()
        fig = px.line(
        cancel_trend,
        x='lead_bin',
        y='bookingscanceled',
        markers=True,
        line_shape='spline',
        color_discrete_sequence=['#e74c3c'],
        title='Average Number of Cancellations vs Lead Time')

        fig.update_layout(
        xaxis_title='Lead Time (Days Before Arrival)',
        yaxis_title='Avg Number of Cancellations')
        st.plotly_chart(fig, use_container_width=True)


        st.markdown("---")


        rev = filtered_df.groupby('marketsegment')['total_revenue'].mean().reset_index()
        seg_cancel = (
            filtered_df.groupby('marketsegment')['bookingscanceled'].sum() /
            filtered_df.groupby('marketsegment')['total_bookings'].sum() * 100
        ).reset_index()

        seg_cancel.columns = ['marketsegment', 'cancel_rate']
        merged = rev.merge(seg_cancel, on='marketsegment') #(one table)

        fig = make_subplots(specs=[[{"secondary_y": True}]]) # (2 y axis char)

        fig.add_trace(
            go.Scatter(
                x=merged['marketsegment'],
                y=merged['total_revenue'],
                name='Revenue',
                mode='lines+markers'
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=merged['marketsegment'],
                y=merged['cancel_rate'],
                name='Cancellation ',
                mode='lines+markers'
            ),
            secondary_y=True
        )
        fig.update_yaxes(title_text="Revenue", secondary_y=False)   
        fig.update_yaxes(title_text="Cancellation", secondary_y=True)
        fig.update_layout(title='Revenue vs Cancellation Rate by Segment')
        st.plotly_chart(fig, use_container_width=True)

        booked = filtered_df.groupby('distributionchannel')['total_bookings'].sum()
        checkedin = filtered_df.groupby('distributionchannel')['bookingscheckedin'].sum()
        canceled = filtered_df.groupby('distributionchannel')['bookingscanceled'].sum()
        noshow = filtered_df.groupby('distributionchannel')['bookingsnoshowed'].sum()

        channel_funnel = pd.DataFrame({
            'distributionchannel': booked.index,
            'booked': booked.values,
            'checkedin': checkedin.values,
            'canceled': canceled.values,
            'noshow': noshow.values
        })

        channel_funnel['conversion_rate'] = (channel_funnel['checkedin'] / channel_funnel['booked'] * 100).round(1)
        channel_funnel['cancel_rate'] = (channel_funnel['canceled'] / channel_funnel['booked'] * 100).round(1)
        channel_funnel['noshow_rate'] = (channel_funnel['noshow'] / channel_funnel['booked'] * 100).round(1)

        fig = px.bar(
            channel_funnel,
            x='distributionchannel',
            y=['conversion_rate', 'cancel_rate', 'noshow_rate'],  
            barmode='group',
            title='Conversion / Cancel / No-show '
        )

        fig.update_traces(marker_color='#2ecc71', selector=dict(name='conversion_rate'))
        fig.update_traces(marker_color='#e74c3c', selector=dict(name='cancel_rate'))
        fig.update_traces(marker_color='#f39c12', selector=dict(name='noshow_rate'))
        fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig.update_layout(yaxis_title='Percentage')
        st.plotly_chart(fig, use_container_width=True)



    with tab3:
        st.subheader("Revenue Analysis")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                x=['Lodging', 'OtherRevenue'],
                y=[filtered_df['lodgingrevenue'].sum(),filtered_df['otherrevenue'].sum()],
                color=['Lodging', 'OtherRevenue'],
                color_discrete_sequence=['#2ecc71', '#e74c3c'],
                labels={'x': 'Revenue Type','y': 'Total Revenue'},
                title='Revenue Sources'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            rev_channel = filtered_df.groupby('distributionchannel')['total_revenue'].sum().reset_index()

            fig = px.bar(
                rev_channel,
                x='distributionchannel',
                y='total_revenue',
                color='total_revenue',
                color_continuous_scale='Blues',
                title='Revenue by Channel'
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        rev_seg = filtered_df.groupby('marketsegment')['total_revenue'].sum().reset_index()

        fig = px.bar(
            rev_seg,
            x='marketsegment',
            y='total_revenue',
            color='total_revenue',
            color_continuous_scale='Blues',
            title='Revenue by Segment'
        )

        st.plotly_chart(fig, use_container_width=True)

        fig = px.scatter(filtered_df,x='roomnights',y='total_revenue',trendline='ols',opacity=0.4,
            title='Room Nights vs Revenue',
            color_discrete_sequence=['#e74c3c']
        )
        st.plotly_chart(fig, use_container_width=True)


        num_df = filtered_df.select_dtypes(include='number')
        corr = num_df.corr()
        revenue_corr = corr['total_revenue'].sort_values(ascending=False)
        revenue_corr = revenue_corr.drop('total_revenue')
        top_features = revenue_corr
        fig = px.bar( x=top_features.values,y=top_features.index,orientation='h',
        color=top_features.values,
        color_continuous_scale='RdBu',
        title="What affects Total Revenue")
        st.plotly_chart(fig, use_container_width=True)

        def cohort_group(x):
            if x <= 30:
                return '0-30 days (New)'
            elif x <= 180:
                return '1-6 months'
            elif x <= 365:
                return '6-12 months'
            else:
                return '1+ year (Old)'

        filtered_df['cohort'] = filtered_df['dayssincefirststay'].apply(cohort_group)
        cohort_analysis = filtered_df.groupby('cohort').agg({
        'total_revenue': 'mean',
        'total_bookings': 'mean',
        'revenue_per_night': 'mean'}).reset_index()
        fig = px.bar(
        cohort_analysis,
        x='cohort',
        y='total_revenue',
        title='Revenue by Customer Cohort')
        st.plotly_chart(fig, use_container_width=True)




    with tab4:
        st.subheader("Customer Insights")

        sr_cols = [
            "srhighfloor","srlowfloor","sraccessibleroom","srmediumfloor",
            "srbathtub","srshower","srcrib","srkingsizebed","srtwinbed",
            "srnearelevator","srawayfromelevator","srnoalcoholinminibar","srquietroom"
        ]

        counts = filtered_df[sr_cols].sum().sort_values()

        fig = px.bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            color=counts.values,
            color_continuous_scale='Greens',
            title='Special Room Requests'
        )

        st.plotly_chart(fig, use_container_width=True)


        nat_counts = booked_df['nationality'].value_counts().reset_index()
        nat_counts.columns = ['nationality', 'count']

        fig = px.choropleth(
            nat_counts,
            locations='nationality',
            color='count',
            color_continuous_scale='Blues',
            title='Customer Distribution by Nationality',
            locationmode='ISO-3'
        )
        fig.update_layout(geo=dict(showframe=False))
        st.plotly_chart(fig, use_container_width=True)



else:

    st.title("Strategic Insights & Recommendations")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Market Segment Analysis", "Customer Value & Risk"]) 


    with tab1:

        st.header("Financial Performance")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Lodging Revenue")
            st.info("""
            **Insight:** Lodging is the main driver of income. However, most transactions are small (Low-value).
            **Analysis:** The hotel relies on many small bookings rather than high-value ones.
            **Recommendation:** Use **Upselling** strategies (offer extra services) during the stay to increase total revenue.
            """)

        with col2:
            st.subheader("Aviation Segment")
            st.warning("""
            **Insight:** High Revenue (600) but High Risk (5.1% cancellation rate).
            **Analysis:** Working with airlines is profitable but unstable.
            **Recommendation:** Apply a **Strict Cancellation Policy** or ask for a higher deposit for airline crews.
            """)

        st.markdown("---")


        st.header("Booking Behavior & Risk")
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Last-Minute Bookings")
            st.error("""
            **Insight:** The main problem is not early bookings, but last-minute ones.
            **Analysis:** Late bookings have the highest risk because customers can easily switch to other hotels.
            **Recommendation:** Require **Pre-payment** for bookings made 48 hours before the check-in date.
            """)

        with col4:
            st.subheader("The Safe Zone (Direct)")
            st.success("""
            **Insight:** Direct bookings are very safe (0.3% cancellation) with good revenue (400).
            **Analysis:** These are our 'Golden Customers' who are loyal and reliable.
            **Recommendation:** Increase the **Marketing Budget** for direct bookings to reduce costs from other channels.
            """)

        st.markdown("---")


        st.header("Loyalty & Operation Efficiency")
        col5, col6 = st.columns(2)

        with col5:
            st.subheader("Customer Loyalty")
            st.markdown("""
            **Insight:** Most customers and agents book only **once**.
            **Analysis:** There is a weakness in keeping customers for a second visit.
            **Recommendation:** Start a **Loyalty Program** with discounts for the second stay.
            """)

        with col6:
            st.subheader("Complementary Rooms")
            st.markdown("""
            **Insight:** Free rooms have low revenue and a high cancellation rate (3.2%).
            **Analysis:** This causes a loss of 'Opportunity Cost' as these rooms could be sold.
            **Recommendation:** Review the policy for free rooms and **reduce them** during busy seasons.
            """)


    with tab2:
        st.header("Customer Value & Risk Analysis")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            with st.container(border=True):
                st.markdown("### High-Value 'Premium' Clients")
                st.write("""
                **Data Insight:** Some customers generate very high revenue (over 9,000) from only 2 or 3 bookings.
                **Recommendation:** Identify these **VIP guests** and offer "Luxury Packages" to ensure they return.
                """)

        with col_v2:
            with st.container(border=True):
                st.markdown("### One-Time Visitors")
                st.write("""
                **Data Insight:** Most clients are concentrated in the low-booking and low-revenue area.
                **Recommendation:** Launch a **Retention Campaign** (like a discount on the 2nd stay) to build loyalty.
                """)

        st.markdown("---")

        col_v3, col_v4 = st.columns(2)
        with col_v3:
            with st.container(border=True):
                st.markdown("### High-Volume Cancellation Risk")
                st.write("""
                **Data Insight:** Customers/Agents with many bookings (>20) show much higher cancellation rates.
                **Recommendation:** Apply a **Volume-Based Cancellation Policy**. Require non-refundable deposits for high-volume accounts.
                """)

        with col_v4:
            with st.container(border=True):
                st.markdown("### Economy Frequent Travelers")
                st.write("""
                **Data Insight:** Guests booking 30-40 times but at low-cost rates.
                **Recommendation:** Implement an **Upselling Strategy** (spa, breakfast) to increase their total contribution.
                """) 

    st.divider()
    st.markdown("""
    **General Note:** Other market segments like **Groups** and **Travel Agents** show strong performance with high profitability and very low cancellation rates, providing a stable base for the hotel.""")
