import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


st.set_page_config(page_title="Hotel Dashboard", layout="wide")

st.sidebar.title("🏨 Hotel Analytics")

df = pd.read_csv('cleaned_hotel_data.csv')

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


    st.subheader("📂 Dataset Preview")
    st.dataframe(filtered_df)


    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🧑‍🤝‍🧑 Total Customers", len(filtered_df))
    col2.metric("💰 Total Revenue", f"${filtered_df['total_revenue'].sum():,.0f}")
    col3.metric("🛏️ Avg Revenue/Night", f"${filtered_df['revenue_per_night'].mean():,.1f}")
    total_v = filtered_df['total_bookings'].sum()

    if total_v > 0:
        calc_rate = (filtered_df['bookingscanceled'].sum() / total_v) * 100
    else:
        calc_rate = 0
    col4.metric("❌ Cancellation Rate", f"{calc_rate:.1f}%")

    st.markdown("---")


elif page == "Analysis":

    st.title("📊 Analysis")

    tab1, tab2, tab3 = st.tabs(["Univariate", "Bivariate", "Multivariate"])

    with tab1:
        st.subheader("Univariate Analysis")
        CHART_HEIGHT = 450
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                filtered_df,
                height=CHART_HEIGHT,
                x='total_bookings',
                title='Distribution of Bookings'
            )
            fig.update_layout(margin=dict(l=20, r=20, t=50, b=50))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            with st.container():
                st.info("The distribution is highly skewed toward low booking counts, indicating limited repeat booking behavior among customers.")
                st.info("The data shows a large number of agents with zero bookings, however the highest concentration is observed at one booking, indicating that most agents generate only a single confirmed booking.")

        with col2:
            fig = px.histogram(
                filtered_df,
                height=CHART_HEIGHT,
                x='total_revenue',
                title='Distribution of Revenue',
                nbins=50
            )

            fig.update_layout(
                xaxis_title="Total Revenue in USD",
                yaxis_title="Count of Customers",
                height=450,
                margin=dict(l=20, r=20, t=50, b=50)
            )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            st.info("The Total Revenue distribution is highly skewed toward 0 and 1, indicating that most revenue is concentrated at low-value transactions.")

        status = pd.DataFrame({
            'Status': ['Checked-in', 'Canceled', 'No-show'],
            'Count': [
                filtered_df['bookingscheckedin'].sum(),
                filtered_df['bookingscanceled'].sum(),
                filtered_df['bookingsnoshowed'].sum()
            ]
        })

        fig = px.pie(status, names='Status', values='Count',
                     title='Booking Status Distribution',color_discrete_sequence=px.colors.qualitative.Set2,)
        st.plotly_chart(fig, use_container_width=True)
        st.info("""Despite the dominance of Check-in (99.7%), the Corporate segment within the distribution channel has the highest cancellation rate among all segments""")


        cat = filtered_df['marketsegment'].value_counts().reset_index()
        cat.columns = ['marketsegment', 'count']

        fig = px.bar(cat, x='marketsegment', y='count',
                     title='Market Segment Distribution',
                     color='marketsegment', 
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)


        total_lodging = filtered_df['lodgingrevenue'].sum()
        total_other = filtered_df['otherrevenue'].sum()

        fig = px.bar(
            x=['Lodging Revenue', 'Other Revenue'],
            y=[total_lodging, total_other],
            title=f'Total Revenue ',
            labels={'x':'Revenue Type', 'y':'Amount'},
            color=['Lodging Revenue', 'Other Revenue'],
            color_discrete_sequence=['#2ecc71','#e74c3c'])
        st.plotly_chart(fig, use_container_width=True)
        st.info("""Lodging Revenue consistently outperforms Other Revenue across all distribution channels and market segments, indicating it as the primary driver of total revenue.""")


    with tab2:
        st.subheader("Bivariate Analysis")


        df = filtered_df.copy()

        df['lead_time_bin'] = pd.cut(
            df['averageleadtime'],
            bins=[0, 30, 60, 90, 180, 365, df['averageleadtime'].max() + 1],
            labels=['0-30', '31-60', '61-90', '91-180', '181-365', '365+'],
            include_lowest=True
        )

        lead_cancel = df.groupby('lead_time_bin', observed=True)[['bookingscanceled', 'total_bookings']].sum()

        lead_cancel['cancellation_rate'] = (
            lead_cancel['bookingscanceled'] / lead_cancel['total_bookings']).fillna(0) * 100

        lead_cancel = lead_cancel.reset_index()
        fig = px.line(
        lead_cancel,
        x='lead_time_bin',
        y='cancellation_rate',
        markers=True,
        title='Cancellation Rate by Booking Lead Time')
        st.plotly_chart(fig, use_container_width=True)
        st.info("""The main issue is not early bookings, but last-minute bookings, as they have the highest cancellation risk and are often made with lower commitment or more flexibility to switch alternatives.""")



        rev = filtered_df.groupby('marketsegment')['total_revenue'].mean().reset_index()

        total_per_seg = filtered_df.groupby('marketsegment')['total_bookings'].sum()
        canceled_per_seg = filtered_df.groupby('marketsegment')['bookingscanceled'].sum()
        cancellation_rate = (canceled_per_seg / total_per_seg) * 100
        seg_stats = cancellation_rate.reset_index()
        seg_stats.columns = ["marketsegment","cancellation_rate"]

        merged = rev.merge(seg_stats, on='marketsegment')
        fig = make_subplots(specs=[[{"secondary_y": True}]])


        fig.add_trace(
            go.Scatter(x=merged['marketsegment'],
                    y=merged['total_revenue'],
                    name="Revenue",
                    mode='lines+markers'),
            secondary_y=False
        )


        fig.add_trace(
            go.Scatter(x=merged['marketsegment'],
                    y=merged['cancellation_rate'],
                    name="Cancellation %",
                    mode='lines+markers'),
            secondary_y=True
        )


        fig.update_layout(title="Revenue vs Cancellation Rate by Market Segment")

        fig.update_yaxes(title_text="Revenue", secondary_y=False)
        fig.update_yaxes(title_text="Cancellation Rate (%)", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)


        st.markdown("### Special Room Requests")
        sr_cols = [
            "srhighfloor","srlowfloor","sraccessibleroom","srmediumfloor",
            "srbathtub","srshower","srcrib","srkingsizebed","srtwinbed",
            "srnearelevator","srawayfromelevator","srnoalcoholinminibar","srquietroom"
        ]

        counts = filtered_df[sr_cols].sum().sort_values()

        fig8 = px.bar(
            x=counts.values,
            y=counts.index,
            color=counts.values,
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig8, use_container_width=True)



    with tab3:
        st.subheader("Multivariate Analysis")


        corr_cols = [
            'total_bookings',
            'total_revenue',
            'bookingscanceled',
            'bookingscheckedin',
            'bookingsnoshowed',
            'dayssincecreation',
            'age'
        ]

        corr = filtered_df[corr_cols].corr()

        fig = px.imshow(corr, text_auto=True,
                        title='Correlation Heatmap')
        st.plotly_chart(fig, use_container_width=True)

        st.write("Bookings strongly affect revenue, cancellation linked to behavior")


        fig = px.scatter(filtered_df,
                         x='total_bookings',
                         y='total_revenue',
                         color='bookingscanceled',
                         title='Bookings vs Revenue vs Cancellation')
        st.plotly_chart(fig, use_container_width=True)

\
else:


    st.title("Strategic Insights & Recommendations")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Market Segment Analysis", "Customer Value & Risk"]) 

    with tab1:
        # 1. Financial & Revenue Performance
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
    **General Note:** Other market segments like **Groups** and **Travel Agents** show strong performance with high profitability and very low cancellation rates, providing a stable base for the hotel.
    """)
