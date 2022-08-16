from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import base64
import numpy

def isnotfloat(num):
    try:
        float(num)
        return False
    except:
        return True

title_png='20220816-Title.png'
title_base64=base64.b64encode(open(title_png,'rb').read()).decode('ascii')

app = Dash(__name__)

app.layout = html.Div([
        html.Div(html.Img(src='data:/image/png;base64,{}'.format(title_base64),style={'display':'block','max-width':'60%','margin':'auto'}),style={'margin':'auto','min-width':'100%'}),
        html.Br(),
        html.Div("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse in enim sed metus tristique 
            tincidunt bibendum non nunc. Vivamus pellentesque hendrerit leo, eget tempor neque rutrum quis. Vivamus ac sem neque. 
            Proin augue metus, pellentesque non elit ut, condimentum accumsan felis. Nulla condimentum rutrum consectetur. Aliquam 
            a est non mi porttitor euismod. Donec arcu urna, efficitur et lorem et, condimentum cursus mauris. Morbi sed volutpat sapien.
            Morbi sit amet ligula arcu. Curabitur convallis blandit velit, id gravida ipsum suscipit a.""",style={'max-width':'500px', 'text-algin':'center','margin-left':'auto','margin-right':'auto'}),
        html.Br(),
        html.Table([html.Tr([html.Td([html.Div(["Expected Throw Distance: ",dcc.Input(id="tot_dis",type='number',min=1,placeholder=1,value=1,autoFocus=True,inputMode="numeric")]),
        html.Br(),
        html.Div(["Number of pans used: ",dcc.Input(id="num_pans",type='number',min=3,placeholder=3,value=3,autoFocus=False,inputMode="numeric",step=2)]),
        html.Br(),
        html.Div(["Separation between pans: ",dcc.Input(id="dis_pans",type='number',min=.001,placeholder=1,value=1,autoFocus=False,inputMode="numeric"),
        html.Br(),
        dcc.RadioItems(['ft', 'yards', 'cm', 'meters'],value='ft'),])]),
        html.Td([html.Div([dash_table.DataTable(
        id='adding-rows-table',
        columns=[{'name': "Pan Number",'id': 'number', 'editable':False, 'deletable':False, 'renamable':False, 'type':'numeric'},{'name': 'Measure of Pan','id': 'weight','deletable': False,'renamable': False,'type': 'numeric','editable':True},{'name': 'Distance from Tractor','id': 'dis','deletable': False,'renamable': False,'type': 'numeric','editable':False}],
        data=[{'number':1,'weight': '0','dis':'0'}],
        editable=True,
        row_deletable=False,
        fill_width=False,
        persistence=True,
        persisted_props = ['data'],
        page_size=10,
        row_selectable='multi',
    ),])])]),
    html.Tr([html.Td([
    dcc.Graph(id='adding-rows-graph'),
    html.Br(),
    dcc.Graph(id='symmetric-normalized-graph'),
    html.Br(),
    html.Div(id='overlap-value'),
    html.Br(),
    dcc.Graph(id='best-overlap'),
    ],colSpan='2')
    ])],style={'max-width':'650px','margin':'auto'})])


@app.callback(
    Output('num_pans','value'),
    Output('dis_pans','value'),
    Output('tot_dis','value'),
    Input('num_pans','value'),
    Input('dis_pans','value'),
    Input('tot_dis','value'),)
def update_inputs(n_pans,d_pans,t_dis):
    if t_dis!=None and n_pans!=None:
        d_pans=float(t_dis/(n_pans-1))
        return n_pans,d_pans,t_dis
    else:
        return n_pans,d_pans,t_dis


@app.callback(
    Output('adding-rows-table', 'data'),
    Input('adding-rows-table', 'selected_rows'),
    Input('num_pans', 'value'),
    Input('dis_pans', 'value'),
    State('adding-rows-table', 'data'),)
def add_row(sel_row,n_rows, sep, rows):
    if n_rows!=None:
        while len(rows)<int(n_rows):
            rows.append({'number': len(rows)+1, 'weight': '0'})
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
    return rows


@app.callback(
    Output('adding-rows-graph', 'figure'),
    Output('symmetric-normalized-graph', 'figure'),
    Input('adding-rows-table', 'data'),)
def display_output(rows):
    #print([k.get('weight') for k in rows])
    #print([k.get('weight') for k in rows[::-1]])
    if len(rows)>0:
        fig=px.line(x=[k.get('dis') for k in rows],y=[float(k.get('weight')) for k in rows],markers=True,line_shape="spline")
        fig.add_bar(x=[k.get('dis') for k in rows],y=[float(k.get('weight')) for k in rows])
        fig.update_layout(xaxis_title='Distance from Tractor',yaxis_title='Measure of Pan',showlegend=False, title={'text':"Raw Data",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
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
        fig2.update_layout(xaxis_title='Distance from Tractor',yaxis_title='Normalized Distribution',showlegend=False, title={'text':"Normalized/Symmetric Data",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
        family="Courier New, monospace",
        size=18,
        color="Black"
        ))
        return fig,fig2

@app.callback(
    Output('best-overlap', 'figure'),
    Output('overlap-value', 'children'),
    Input('adding-rows-table', 'data'),
    Input('dis_pans', 'value'),
)
def calc_best_overlap(rows,sep):
    if len(rows)>0:
        rawy=numpy.add([float(k.get('weight')) for k in rows],[float(k.get('weight')) for k in rows[::-1]])
        total=numpy.sum(rawy)
        if total!=0:
            normy=numpy.divide(rawy,total)
        else:
            normy=0
        var=[]
        for k in range(1,int(len(rows)/2)):
            padleft=numpy.pad(normy,(2*k,0),mode='constant',constant_values=0)
            padright=numpy.pad(normy,(0,2*k),mode='constant',constant_values=0)
            padmid=numpy.pad(normy,(k,k),mode='constant',constant_values=0)
            padlrm=numpy.add(numpy.add(padleft,padright),padmid)
            padlrm=padlrm[k:-k]
            total=numpy.sum(padlrm)
            normlrm=numpy.divide(padlrm,total)
            var.append(numpy.var(normlrm))
        if numpy.sum(var)!=0:
            #print(numpy.min(var))
            pass
        else:
            var=[1,2,3]
        optpath=numpy.argmin(var)
        padleft=numpy.pad(normy,(2*optpath,0),mode='constant',constant_values=0)
        padmid=numpy.pad(normy,(optpath,optpath),mode='constant',constant_values=0)
        padright=numpy.pad(normy,(0,2*optpath),mode='constant',constant_values=0)
        padlrm=numpy.add(numpy.add(padleft,padright),padmid)
        total=numpy.sum(padlrm)
        normlrm=numpy.divide(padlrm,total)
        normlrm=normlrm[optpath:-optpath]
        xs=[k.get('dis') for k in rows]
        for k in range(0,optpath):
            xs.insert(0,xs[0]-sep)
            xs.insert(len(xs),xs[len(xs)-1]+sep)
        fig=px.line(x=xs[optpath:-optpath],y=normlrm,markers=True,line_shape="spline")
        fig.add_bar(x=xs[optpath:-optpath],y=normlrm)
        fig.update_layout(xaxis_title='Distance from Tractor',yaxis_title='Measure of Pan',showlegend=False, title={'text':"Optimized Path Distribution",'y':0.95,'x':0.5,'xanchor':'center','yanchor':'top'},font=dict(
        family="Courier New, monospace",
        size=18,
        color="Black"
        ))
        return fig,"The optimized overlap is: "+str(numpy.argmin(var)*sep)+" units between passes."





if __name__ == '__main__':
    app.run_server(debug=True)