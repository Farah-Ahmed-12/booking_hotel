import streamlit as st
import pandas as pd
import plotly.express as px


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

revenue_filter = st.sidebar.slider(
    'Total Revenue Range',
    float(df['total_revenue'].min()),
    float(df['total_revenue'].max()),
    (float(df['total_revenue'].min()), float(df['total_revenue'].max()))
)

bookings_filter = st.sidebar.slider(
    'Total Bookings Range',
    int(df['total_bookings'].min()),
    int(df['total_bookings'].max()),
    (int(df['total_bookings'].min()), int(df['total_bookings'].max()))
)


filtered_df = df[
    (df['nationality'].isin(nationality_filter)) &
    (df['distributionchannel'].isin(channel_filter)) &
    (df['marketsegment'].isin(market_filter)) &
    (df['age'].between(age_filter[0], age_filter[1])) &
    (df['total_revenue'].between(revenue_filter[0], revenue_filter[1])) &
    (df['total_bookings'].between(bookings_filter[0], bookings_filter[1]))
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
    col4.metric(
        "❌ Cancellation Rate",
        f"{filtered_df['bookingscanceled'].sum() / filtered_df['total_bookings'].sum() * 100:.1f}%"
    )

    st.markdown("---")


elif page == "Analysis":

    st.title("📊 Analysis")

    tab1, tab2, tab3 = st.tabs(["Univariate", "Bivariate", "Multivariate"])


    with tab1:
        st.subheader("Univariate Analysis")

        col1, col2 = st.columns(2)


        with col1:
            fig = px.histogram(filtered_df, x='total_bookings',title='Distribution of Bookings')
            st.plotly_chart(fig, use_container_width=True)


        with col2:
            fig = px.histogram(filtered_df, x='total_revenue',
                               title='Distribution of Revenue',nbins=50,
                               range_x=[0, df['lodgingrevenue'].max()])
            fig.update_layout(
            xaxis_title="Total Revenue in USD",
            yaxis_title="Count of Customers",
            height=500)
            st.plotly_chart(fig, use_container_width=True)


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



    with tab2:
        st.subheader("Bivariate Analysis")


        filtered_df['is_canceled'] = filtered_df['bookingscanceled'].apply(
            lambda x: "Canceled" if x > 0 else "Not Canceled"
        )

        fig = px.box(filtered_df,
                     x='is_canceled',
                     y='dayssincecreation',
                     title='Cancellation vs Customer Tenure',
                     color='bookingscanceled',
                     color_discrete_sequence=['#3498db', '#e67e22'])
        st.plotly_chart(fig, use_container_width=True)


        rev = filtered_df.groupby('marketsegment')['total_revenue'].mean().reset_index()

        fig = px.bar(rev,
                     x='marketsegment',
                     y='total_revenue',
                     title='Revenue by Market Segment',
                     color='total_revenue', 
                     color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)


        total_per_seg = filtered_df.groupby('marketsegment')['total_bookings'].sum()
        canceled_per_seg = filtered_df.groupby('marketsegment')['bookingscanceled'].sum()

        cancellation_rate = (canceled_per_seg / total_per_seg) * 100
        seg_stats = cancellation_rate.reset_index()
        seg_stats.columns = ["marketsegment","cancellation_rate"]
        seg_stats = seg_stats.sort_values('cancellation_rate',ascending=False)

        fig = px.bar(seg_stats , x='marketsegment' ,y='cancellation_rate',
             text='cancellation_rate',
             color='cancellation_rate', color_continuous_scale='Reds',
             title='Cancellation Rate by Distribution Segment'

)
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
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
    st.title("💡 Insights & Recommendations")

    st.write("""
             # 📊 Distribution of Bookings
📊 Customer Engagement:
- A large proportion of customers have zero bookings, indicating low engagement.

📊 Revenue Insights:
- Revenue is mainly concentrated in lodging, showing underutilization of auxiliary services.
- Aviation and high-value segments generate the highest revenue but come with higher cancellation risk.
- Direct, Corporate, and Group bookings are more stable with lower cancellation rates.
- Customer demand is concentrated in King and Twin room types.
- The "Other" segment drives most booking volume but lower revenue contribution.

📊 Booking Behavior & Tenure:
- Long-tenure customers have higher cancellation rates than newer customers.
- Cancellations are more common among customers who book far in advance.
- New customers tend to book closer to travel dates and cancel less often.

📌 Recommendations:
- Focus on high-value segments (especially Aviation) while managing cancellation risk.
- Increase direct bookings to improve profitability and reduce costs.
- Introduce VIP and loyalty programs for high-spending customers.
- Promote upselling (spa, breakfast, transport, late checkout).
- Strengthen cancellation policies for early bookings (6+ months).
- Offer non-refundable options with incentives.
- Improve and expand ancillary revenue streams. """)
