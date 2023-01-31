from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import base64
import numpy
from scipy.stats import variation 

def isnotfloat(num):
    try:
        float(num)
        return False
    except:
        return True

title_png='20230130-Title-Rev2.png'
title_base64=base64.b64encode(open(title_png,'rb').read()).decode('ascii')

app = Dash(__name__)

server=app.server

app.layout = html.Div([
        html.Div(html.Img(src='data:/image/png;base64,{}'.format(title_base64),style={'display':'block','max-width':'60%','margin':'auto'}),style={'margin':'auto','min-width':'100%'}),
        html.Br(),
        html.Div([
            html.Div("""This tool computes the optimal swath width for a granulat applicator based on data from a pan test."""),
            html.Br(),
            html.Div("""1)	Input the number of pans used to collect the dispersed media under “Number of pans used”.  Include pans removed for tire clearance in the count.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'10px','margin-right':'auto'}),
            html.Br(),
            html.Div("""2)	Input the value for the pan sapcing and choose the corresponding units.  The blue-highlighted cell is the center of the machine.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'10px','margin-right':'auto'}),
            html.Br(),
            html.Div("""3)	On the table to the right, input a numeric value for the amount of material measured in each pan.  Units are not critical as long as all pans are measured in the same way.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'10px','margin-right':'auto'}),
            html.Br(),
            html.Div("""4)	If an amount for a pan is unknown (pans removed for tire clearance, or one got spilled), mark the the checkbox to the left of the corresponding "Pan Number".  The calculator will estimate a value for that pan as the average of the adjacent pans.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'10px','margin-right':'auto'}),
            html.Br(),
            html.Div("""5)	Four plots are automatically generated:""",style={'max-width':'500px', 'text-algin':'center','margin-left':'10px','margin-right':'auto'}),
            html.Div("""i.	Spread Pattern – The calibration pan measurements plotted against the distance from center.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'30px','margin-right':'auto'}),
            html.Br(),
            html.Div("""ii. Normalized/Symmetric Pattern – This plot represents the average of the left-hand and right-hand data to better approximate overlapping passes.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'30px','margin-right':'auto'}),
            html.Br(),
            html.Div("""iii.	CV vs Swath Width – This plot shows the amount of variation you would expected across adjacent passes.  It is measured by the Coefficient of Variation (CV), which is a statistical measure of numeric variation.  The slider allows the user to change the swath width to illustrate how the CV changes with swath width.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'30px','margin-right':'auto'}),
            html.Br(),
            html.Div("""iv. Optimized Path Distribution – This plot displays the expected distribution of material from the center of one pass to the center of the adjacent pass.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'30px','margin-right':'auto'}),
            html.Br(),
        ],style={'max-width':'500px', 'text-algin':'center','margin-left':'auto','margin-right':'auto'}),
        html.Table([html.Tr([html.Td([
        html.Div(["Number of pans used: ",dcc.Input(id="num_pans",type='number',min=3,placeholder=3,value=3,autoFocus=False,inputMode="numeric",step=2,debounce=True)]),
        html.Br(),
        html.Div(["Pan Spacing: ",dcc.Input(id="dis_pans",type='number',min=.001,placeholder=1,value=1,autoFocus=False,inputMode="numeric",debounce=True),
        html.Br(),
        dcc.RadioItems(['in', 'ft', 'cm', 'meters'],value='ft',id="units"),])]),
        html.Td([html.Div([dash_table.DataTable(
        id='adding-rows-table',
        columns=[{'name': "Pan Number",'id': 'number', 'editable':False, 'deletable':False, 'renamable':False, 'type':'numeric'},{'name': 'Amount in Pan','id': 'weight','deletable': False,'renamable': False,'type': 'numeric','editable':True},{'name': 'Distance from Center','id': 'dis','deletable': False,'renamable': False,'type': 'numeric','editable':False}],
        data=[],
        row_deletable=False,
        fill_width=False,
        persistence=True,
        row_selectable='multi',
        style_data_conditional=[{
            'if': {
                'filter_query': '{number} = 2'
            },
            'backgroundColor': 'dodgerblue',
            'color': 'white'
        }]
    ),])])]),
    html.Tr([html.Td([
    dcc.Graph(id='adding-rows-graph'),
    html.Br(),
    dcc.Graph(id='symmetric-normalized-graph'),
    html.Br(),
    html.Div(id='overlap-value',style={'font-size':24, 'font-weight':'bold'}),
    ],colSpan='2')]),
    html.Tr([html.Td([
        dcc.Slider(0,1,1,id='swath-slider',value=1),
        html.Br(),
        dcc.Graph(id='best-overlap'),
        html.Br(),
        dcc.Graph(id='swath-dist'),
        ],colSpan='2')
    ])],style={'max-width':'650px','margin':'auto'})])

@app.callback(
    Output('num_pans','value'),
    Output('dis_pans','value'),
    Input('num_pans','value'),
    Input('dis_pans','value'),
)
def fix_blanks(n_pans,d_pans):
    if n_pans==None:
        n_pans=3
    if d_pans==None:
        d_pans=1
    return n_pans,d_pans

@app.callback(
    Output('adding-rows-table', 'data'),
    Output('swath-slider', 'max'),
    Output('swath-slider', 'min'),
    Output('swath-slider','step'),
    Input('adding-rows-table', 'selected_rows'),
    Input('num_pans', 'value'),
    Input('dis_pans', 'value'),
    State('adding-rows-table', 'data'),prevent_initial_call=True)
def add_row(sel_row,n_rows, sep, rows):
    temp_rows=[]
    if n_rows!=None:
        while len(rows)<int(n_rows):
            rows.append({'number': len(rows)+1, 'weight': 0})
        while len(rows)>int(n_rows):
            rows.pop()
    if sep!=None:
        for i in range(len(rows)):
            if len(rows)%2==1:
                rows[i]['dis']=float(int(len(rows)/2)-len(rows)+i+1)*float(sep)
            else:
                rows[i]['dis']=float((-len(rows)/2+.5+i)*sep)
    if sel_row!=None:
        print(sel_row)
        for i in range(len(sel_row)):
            #print(len(rows))
            #print(sel_row[0])
            if sel_row[i]!=0 and sel_row[i]!=len(rows):
                print(rows[sel_row[i]])
                rows[sel_row[i]]['weight']=float((float(rows[sel_row[i]+1]['weight'])+float(rows[sel_row[i]-1]['weight']))/2.0)
    return rows,int(n_rows-1)*sep,3*sep,sep
    
@app.callback(
    Output('adding-rows-table', 'style_data_conditional'),
    Input('num_pans', 'value'),
)
def update_trac_location(n_rows):
    style=[
        {
            'if': {
                u'filter_query': '{{number}} = {}'.format(str(int(n_rows/2)+1))
            },
            'backgroundColor': '#0033a0',
            'color': 'white'
        }]
    return style

@app.callback(
    Output('adding-rows-graph', 'figure'),
    Output('symmetric-normalized-graph', 'figure'),
    Input('adding-rows-table', 'data'),)
def display_output(rows):
    fig=px.line(x=[k.get('dis') for k in rows],y=[float(k.get('weight')) for k in rows],markers=True,line_shape="spline")
    fig.add_bar(x=[k.get('dis') for k in rows],y=[float(k.get('weight')) for k in rows])
    fig.update_layout(xaxis_title='Distance from Center',yaxis_title='Amount In Pan',showlegend=False, title={'text':"Spread Pattern",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
    family="Courier New, monospace",
    size=18,
    color="Black"
    ))
    y2=numpy.add([float(k.get('weight')) for k in rows],[float(k.get('weight')) for k in rows[::-1]])
    total=float(numpy.sum(y2))
    if total==0:
        total=float(1)
    fig2=px.line(x=[k.get('dis') for k in rows],y=numpy.divide(y2,total),markers=True,line_shape="spline")
    fig2.add_bar(x=[k.get('dis') for k in rows],y=numpy.divide(y2,total))
    fig2.update_layout(xaxis_title='Distance from Center',yaxis_title='Normalized Distribution',showlegend=False, title={'text':"Normalized/Symmetric Pattern",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
    family="Courier New, monospace",
    size=18,
    color="Black"
    ))
    return fig,fig2

@app.callback(
        Output('swath-slider', 'value'),
        Output('overlap-value', 'children'),
        Input('adding-rows-table', 'data'),
        Input('dis_pans', 'value'),
        Input('units','value')
)
def calc_opt(rows,sep,units):
    rawy=numpy.add([float(k.get('weight')) for k in rows],[float(k.get('weight')) for k in rows[::-1]])
    total=numpy.sum(rawy)
    if total!=0:
        normy=numpy.divide(rawy,total)
    else:
        normy=0
    var=[]
    for k in range(3,int(len(rows))):
        padleft=numpy.pad(normy,(k,0),mode='constant',constant_values=0)
        padright=numpy.pad(normy,(0,k),mode='constant',constant_values=0)
        shifted=numpy.add(padleft,padright)
        shifted=shifted[int(len(rows)/2):int(len(rows)/2)+k]
        total=numpy.sum(shifted)
        normlrm=numpy.divide(shifted,total)
        var.append(variation(shifted,ddof=1)*100.0)
    if numpy.sum(var)!=0:
        pass
    else:
        var=[1,2,3]
    optpath=numpy.max(numpy.argwhere(numpy.sign(numpy.gradient(var))==-1))
    return (optpath+4)*sep,"The optimal swath width is: "+str((optpath+4)*sep)+" "+str(units)+" between passes."

@app.callback(
    Output('best-overlap', 'figure'),
    Input('swath-slider','value'),
    Input('adding-rows-table', 'data'),
    Input('dis_pans', 'value'),
)
def calc_best_overlap(sliderloc,rows,sep):
    rawy=numpy.add([float(k.get('weight')) for k in rows],[float(k.get('weight')) for k in rows[::-1]])
    total=numpy.sum(rawy)
    if total!=0:
        normy=numpy.divide(rawy,total)
    else:
        normy=0
    var=[]
    for k in range(3,int(len(rows))):
        padleft=numpy.pad(normy,(k,0),mode='constant',constant_values=0)
        padright=numpy.pad(normy,(0,k),mode='constant',constant_values=0)
        shifted=numpy.add(padleft,padright)
        shifted=shifted[int(len(rows)/2):int(len(rows)/2)+k]
        total=numpy.sum(shifted)
        normlrm=numpy.divide(shifted,total)
        var.append(variation(shifted,ddof=1)*100.0)
    if numpy.sum(var)!=0:
        pass
    else:
        var=[1,2,3]
    fig=px.line(x=numpy.multiply(numpy.arange(3,int(len(rows))),sep),y=var)
    fig.update_layout(xaxis_title='Swath Width',yaxis_title='CV',showlegend=False, title={'text':"CV vs. Swath Width",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
    family="Courier New, monospace",
    size=18,
    color="Black"
    )
    )
    fig.add_vline(x=sliderloc, line_width=3, line_dash="dash", line_color="#0033a0")

    return fig

@app.callback(
    Output('swath-dist', 'figure'),
    Input('swath-slider','value'),
    Input('adding-rows-table', 'data'),
    Input('dis_pans', 'value'),
)
def output_dis(sliderloc,rows,sep):
    rawy=numpy.add([float(k.get('weight')) for k in rows],[float(k.get('weight')) for k in rows[::-1]])
    total=numpy.sum(rawy)
    if total!=0:
        normy=numpy.divide(rawy,total)
    else:
        normy=0
    value=int(sliderloc/sep)
    padleft=numpy.pad(normy,(value,0),mode='constant',constant_values=0)
    padright=numpy.pad(normy,(0,value),mode='constant',constant_values=0)
    padlrm=numpy.add(padleft,padright)
    padlrm=padlrm[int(len(rows)/2):int(len(rows)/2+value+1)]
    total=numpy.sum(padlrm)
    normlrm=numpy.divide(padlrm,total)
    xs=[]
    j=0
    for k in range(int(len(rows)/2),int(len(rows)/2)+value+1):
        xs.append(j*sep)
        j+=1
    fig=px.line(x=xs,y=normlrm,markers=True,line_shape="spline")
    fig.add_bar(x=xs,y=normlrm)
    fig.update_layout(yaxis_title=' ',xaxis_title='Distance from Center',showlegend=False, title={'text':"Expected Distribution Between Swaths",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
    family="Courier New, monospace",
    size=18,
    color="Black"
    ))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)