#Attempt 3
import json
import streamlit as st
import pandas as pd
from appinsights_api import call_api
from chartsframe import langchain_charts
from prompts import langchain_qa
from functools import partial

st.set_page_config(layout='wide')
st.title("ObservabilityGPT")

table_tab = None
chart_tab = None

table_container = None
chart_container = None
side_bar_container = None

st.markdown("""
    <style>
    .developer-names {
        position: absolute;
        top: -155px;
        left: -60px;
    }
    </style>
    <div class="developer-names">
        <h4>Created by Tim Zelikovsky & Madhukar Anugu Summer 2023</h4>
    </div>
    """, unsafe_allow_html=True)


# Initialize the global counter
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Initialize the expander counter
if 'expander_counter' not in st.session_state:
    st.session_state.expander_counter = 0

if 'all_queries_processed' not in st.session_state:
    st.session_state.all_queries_processed = False

# Predefined queries
queries = [
    #1: number of requests by time stamp
    "requests | summarize NumberOfRequests=count() by bin(timestamp, 5m) ",
    #2: Response time trend
    "requests | where timestamp > ago(12h) | summarize avgRequestDuration=avg(duration) by bin(timestamp, 10m)",
    #3: Named sessions
    #"let usg_events = dynamic([""*""]); let grain = iff(true, 1h, 1h); let mainTable = union pageViews, customEvents, requests | where timestamp > ago(1d) | where isempty(operation_SyntheticSource) | extend name =replace(""\n"", """", name) | extend name =replace(""\r"", """", name) | where '*' in (usg_events) or name in (usg_events); let resultTable = mainTable; resultTable | make-series Sessions = dcount(session_Id) default = 0 on timestamp from ago(1d) to now() step grain",
    #4: Events (broken)
    #"let usg_events = dynamic([""*""]); let grain = iff(true, 1h, 1h); let mainTable = union pageViews, customEvents, requests | where timestamp > ago(1d) | where isempty(operation_SyntheticSource) | extend name =replace(""\n"", """", name) | extend name =replace(""\r"", """", name) | where '*' in (usg_events) or name in (usg_events); let resultTable = mainTable; resultTable | make-series Events = count() default = 0 on timestamp from ago(1d) to now() step grain",
    #5: Top 10 exceptions by occurence (broken)
    "exceptions | summarize count() by type | top 10 by count_desc",
    #6: Top 10 slowest requests (broken)
    #"requests | summarize _90thPercentileDuration = percentile(duration, 90) by name | join kind=leftouter (requests) on $left.name == $right.name | distinct name, _90thPercentileDuration, appName, iKey, sdkVersion, _ResourceId | extend durationSeconds =  _90thPercentileDuration / 1000 | project name, durationSeconds, appName, iKey, sdkVersion, _ResourceId | top 10 by durationSeconds",
    #7: Top 10 slowest dependencies calls (doesn't even use it)
    #"dependencies| summarize _90thPercentileDuration = percentile(duration, 90) by name | join kind=leftouter (dependencies) on $left.name==$right.name | distinct name, _90thPercentileDuration, appName, iKey, sdkVersion, _ResourceId | extend durationSeconds = _90thPercentileDuration / 1000 | top 10 by _90thPercentileDuration desc | project name, durationSeconds, appName, iKey, sdkVersion, _ResourceId",
    #8: Top 10 Browser Errors
    #"let timeGrain=5m; let dataset=exceptions | where client_Type == ""Browser""; dataset | summarize count_=sum(itemCount), impactedUsers=dcount(user_Id) by problemId | union(dataset | summarize count_=sum(itemCount), impactedUsers=dcount(user_Id) | extend problemId=""Overall"") | where count_ > 0 | order by count_ desc | top 11 by count_",
    #9: Top 401 Errors
    #"Requests | where StatusCode == 401 | order by Duration desc | extend RequestDetails = strcat(""Request ID: "", RequestID, "", Duration: "", toString(Duration)) | top 10 by Duration desc | project RequestDetails",
    #10: Number of Returns Completed
    "requests | where name == ""POST CompleteReturn/CompleteReturn"" | summarize Returns = dcount(tostring(customDimensions.returnId)) by bin(timestamp, 1h))",
    #11: Number of Returns Created
    "requests | where name == ""POST CreateReturn/CreateReturn"" or name == ""POST Return/ImportProforma"" | summarize TotalReturnsCreated = count() by bin(timestamp, 30m))",
    #12: Number of Returns Active per Second
    "requests | make-series Returns = dcount(tostring(customDimensions.returnId)) on timestamp = todatetime(timestamp) in range(ago(1d), now(), 1m) | mv-expand timestamp, Returns | project todatetime(timestamp), toint(Returns) | top 100 by timestamp",
    #13: Field Saves Per Return (Sample)
    "customEvents | where name == ""redis_cache_write_time"" | where operation_Name == ""POST DataCacheWriter/Save"" | where tostring(customDimensions.returnId) != """" and strlen(tostring(customDimensions.returnId)) < 45 | summarize NumberOfFieldSavesPerReturn = count() by tostring(customDimensions.returnId) | sample 100,title = strcat(""Field Saves Per Return (Average: "", tostring(toscalar(customEvents | where name == ""redis_cache_write_time"" | where tostring(customDimensions.returnId) != """" and strlen(tostring(customDimensions.returnId)) < 45 | summarize NumberOfFieldSavesPerReturn = count() by tostring(customDimensions.returnId) | summarize avg(NumberOfFieldSavesPerReturn))), "")""))",
    #14: Page Saves per return (sample)
    "requests | where name == ""POST Page/Save"" | summarize NumberOfPageSavesPerReturn = count() by tostring(customDimensions.returnId) | sample 20)",
    #15: Average number of page saves
    "requests | where name == ""POST Page/Save"" | summarize NumberOfPageSavesPerReturn = count() by tostring(customDimensions.returnId) | summarize round(avg(NumberOfPageSavesPerReturn),3)",
    #16: Returns Created Per Office and Per Tax Pro
    "requests | where name contains ""POST OpenReturn/OpenReturn"" | extend OfficeId = tostring(customDimensions.officeId) , TaxProId = tostring(customDimensions.taxProId), ReturnId = tostring(customDimensions.returnId) | summarize  DistinctOpenReturnCount = dcount(ReturnId) by name, OfficeId, TaxProId | sort by DistinctOpenReturnCount desc",
    #17: Engine Calls Per Return
    "dependencies | where name contains ""api/diag"" | summarize EngineCallsPerReturn = count() by tostring(customDimensions.returnId) | take 100 )"
]
def displayDataAndChart(tab_container, char_container):
    selected = st.session_state.selected
    if selected is not None:
        query_response = selected.get('Response')
        data = call_api(query_response)
        if data is None or not isinstance(data, dict):
            st.error("No data received from API call.")
            return
        displayAppInsightsData(selected, data, tab_container, char_container)

def on_history_select(query_resp, tab_container, char_container):
    st.session_state.__setitem__('selected', query_resp)
    displayDataAndChart(tab_container, char_container)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def displayAppInsightsData(selected, data, tab_container, char_container):
    tables = data['tables']
    parsed = {}

    for table in tables:
        parsed[table['name']] = pd.DataFrame.from_records(table['rows'],
                                                          columns=[col['name'] for col in table['columns']])
    print('parsing done')
    df = parsed['PrimaryResult']
    st.write(f"Total Records: {df.shape[0]}")
    response_query = selected.get('query')
    response_answer = selected.get('Response')
    sample_df = df.iloc[:2]
    charts_answer = langchain_charts(response_query, response_answer, sample_df)
    if tab_container is None:
        tab_container = st.container()
    if char_container is None:
        char_container = st.container()
    with tab_container:
        tab_container.empty()
        tab_container.write("Table")
        tab_container.dataframe(df)
    with char_container:
        char_container.empty()
        char_container.write("Chart")
        fields = []
        if charts_answer is not None and charts_answer.find('Answer:') > -1:
            final_charts_answer = charts_answer[charts_answer.find('Answer:') + 7:]
            final_charts_answer = final_charts_answer.lstrip()
            fields = final_charts_answer.split(',')
        chart_type = None
        xcol = None
        ycol = None
        chart_title = ''
        for field in fields:
            if 'chartType' in field:
                chart_value = field.replace('chartType:', '')
                if 'unknown' in chart_value:
                    char_container.write('Unable to determine chart type')
                    char_container.table(fields)
                else:
                    chart_type = chart_value
            elif 'chartTitle' in field:
                chart_title = field.replace('chartTitle:', '')
            elif 'xcol' in field:
                column_value = field.replace('xcol:', '')
                xcol = column_value.strip()
            elif 'ycol' in field:
                column_value = field.replace('ycol:', '')
                ycol = column_value.strip()
        if chart_title is not None:
            char_container.write(chart_title)
        if chart_type is not None:
            chart_type = chart_type.strip().lower()
            if xcol is not None and ycol is not None:
                new_df = df[[xcol, ycol]].copy()
                new_dict = new_df.to_dict('records')
                graph = char_container.container()
                char_container.button('Line Chart', key=f"lineBtn_{st.session_state.expander_counter}",
                                      on_click=lambda: graph.line_chart(new_dict, x=xcol, y=ycol,
                                                                        use_container_width=True))
                char_container.button('Bar Chart', key=f"barBtn_{st.session_state.expander_counter}",
                                      on_click=lambda: graph.bar_chart(new_dict, x=xcol, y=ycol,
                                                                       use_container_width=True))
                if 'line' in chart_type:
                    graph.line_chart(new_dict, x=xcol, y=ycol, use_container_width=True)
                elif chart_type == 'bar':
                    graph.bar_chart(new_dict, x=xcol, y=ycol, use_container_width=True)
                else:
                    char_container.write(f'add more chart types {chart_type}')

# Initialize responses in session state
if 'responses' not in st.session_state:
    st.session_state.responses = []

# Define navigation functions
def on_start_select():
    st.session_state.screen = 2
    #st.experimental_rerun()

def on_back_select():
    st.session_state.screen = 1
    #st.experimental_rerun()

def on_how_to_use_select():
    st.session_state.screen = 3
    #st.experimental_rerun()
def handle_query(query):
    if query == queries[-1]:
        st.session_state.all_queries_processed = True
    response = langchain_qa(query)
    answer = response.get('answer')
    if "kusto query:" not in answer.lower():
        st.info(answer)
        pass
    else:
        answer = answer.replace('Kusto Query:', '')
        if 'reason' in answer.lower():
            st.error(answer)
        else:
            answer = answer.lstrip()
            resp = {'Response': answer, 'query': query}
            st.session_state.responses.append(resp)
            st.success(answer)
            st.session_state['selected'] = resp
            table_tab, chart_tab = st.tabs(["Table", "Chart"])
            with table_tab:
                table_container = st.container()
            with chart_tab:
                chart_container = st.container()
            if side_bar_container is not None:
                side_bar_container.empty()
                with side_bar_container:
                    st.write('History')
                    for response in st.session_state.responses:
                        with st.expander(f"Response {st.session_state.expander_counter + 1}"):
                            hist_container = st.container()
                            with hist_container:
                                st.info(response['query'])
                                st.success(response['Response'])
                                st.session_state.expander_counter += 1 #increment expander counter
                                select_key = f"SelectRespBtn_{st.session_state.expander_counter + 1}"
                                st.session_state.counter += 1 # increment the global counter
                                print(f"Creating select button with key: {select_key}")
                                if not st.session_state.get(select_key):
                                    st.button("Select", key=select_key,
                                              on_click=partial(on_history_select, response, table_container,
                                                               chart_container))
                                delete_key = f"DelRespBtn_{st.session_state.counter}"
                                st.session_state.counter += 1  # Increment the global counter
                                print(f"Creating delete button with key: {delete_key}")
                                if not st.session_state.get(delete_key):
                                    st.button("Delete", key=delete_key, on_click=partial(on_history_select, response, table_container, chart_container))

                        displayDataAndChart(table_container, chart_container)


# Initialize screen state
if 'screen' not in st.session_state:
    st.session_state.screen = 1

# Screen 1: Welcome Screen
if st.session_state.screen == 1:
    #st.markdown("# ObservabilityGPT")

    st.button("Start", on_click=on_start_select, key="start_button_welcome")
    #st.button("How To Use", on_click=on_how_to_use_select, key="how_to_use_button_welcome")

# Screen 2: Main Functionality
elif st.session_state.screen == 2:
    # ... your code for the start screen ...
    local_css("static/style.css")
    st.info('Retrieves Azure App Insights Through a Natural Language Request')
    with st.sidebar:
        side_bar_container = st.container()
        with side_bar_container:
            st.write('')

    # Your main functionality code
    query = st.text_input("What would you like displayed from Azure App Insights?")
    if st.button("Submit", key="submitBtn"):
        if query.strip() == "":
            st.error("Please enter a valid query.")
        else:
            handle_query(query) #new method
    if st.button("Generate Dashboards", key="generateBtn"):
        # Only process queries if not all of them have been processed yet
        if not st.session_state.all_queries_processed:
            # Run the dashboard generation function for each query
            for query in queries:
                # Handle each predefined query
                handle_query(query)
        else:
            st.write("All queries have been processed. ")

    st.button("Back", on_click=on_back_select, key="back_button_functionality")

