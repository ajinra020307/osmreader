import xml.dom.minidom
from decimal import Decimal

def readOsmAsXml(osmfilepath):
    data=xml.dom.minidom.parse(osmfilepath)
    return data

def getStartPointsOfWays(ways):
    start_points=[]
    for way in ways:
        points_in_current_way=getPointsInTheWay(way,False)
        start_points.append({"point":points_in_current_way[0],'way':way})
    return start_points

def findHighways(ways):
    highways=[]
    for way in ways:
        tags=way.getElementsByTagName('tag')
        inhighway_class=False
        has_name=False
        has_turn_lanes=False
        highway_class = ["primary", "motorway_link", "motorway"]
        #in primary we does not handle the condition where the turn lanes are on the right and left
        for tag in tags:
            if(tag.getAttribute('k')=="turn:lanes"):
                has_turn_lanes=True

        if True:#if it does not had turn lanes add the highway
            for tag in tags:
                if tag.getAttribute('k')=="highway" and tag.getAttribute('v') in highway_class:
                    inhighway_class=True
                if tag.getAttribute('k')=='name' or tag.getAttribute('k')=='reg_name':
                    has_name=True
                if has_name and inhighway_class:
                    highways.append(way)
                    break

    return highways

def getPointsInTheWay(way,fullnodereq):
    nodes=[]
    fullnodes=[]
    points = way.getElementsByTagName('nd')
    for point in points:
        fullnodes.append(point)
        nodes.append(point.getAttribute('ref'))
    if fullnodereq:
        return fullnodes
    return nodes

def findWaysStartAtThisPoint(start_points,current_point):
    ways=[]
    for start_point in start_points:
        if current_point==start_point["point"]:   
            ways.append(start_point["way"])
    return ways


def findContinuationAndNonContinousPoint(ways,main_way):
    main_name=None
   
    for node in main_way.getElementsByTagName('tag'):
        if node.getAttribute('k')=='name':
            main_name=node.getAttribute('v')
        elif node.getAttribute('k')=='reg_name':
            main_name = node.getAttribute('v')

    if main_name:
        for i,way in enumerate(ways):
            for node_index,node in enumerate(way.getElementsByTagName('tag')):
                if node.getAttribute('k')=='name' and node.getAttribute('v')==main_name:
                    continous_way=way
                    if i==0:
                        non_continous_way=ways[1]
                        return {"continous_way": continous_way, "non_continous_way": non_continous_way}
                    elif i==1:
                        non_continous_way=ways[0]
                        return {"continous_way": continous_way, "non_continous_way": non_continous_way}
                elif node.getAttribute('k')=='reg_name' and node.getAttribute('v')==main_name:
                    continous_way = way
                    if i == 0:
                        non_continous_way=ways[1]
                        return {"continous_way": continous_way, "non_continous_way": non_continous_way}
                    elif i == 1:
                        non_continous_way=ways[0]
                        return {"continous_way": continous_way, "non_continous_way": non_continous_way}

    else:
        raise KeyError


def findNoOfLanes(way):
    tags=way.getElementsByTagName('tag')
    for tag in tags:
        if tag.getAttribute('k')=="lanes":
            return int(tag.getAttribute('v'))
    else:
        return 1

def findAPoint(way,nodes,point_no): 
    nd=way.getElementsByTagName('nd')
    for i,point in enumerate(nd):
        if i==point_no:
            ref=point.getAttribute('ref')
            for node in nodes:
                if node.getAttribute('id')==ref:
                    lat=node.getAttribute('lat')
                    lon=node.getAttribute('lon')
                    return {"x":lat,"y":lon}

        

def getLaneSide(v1,v2,common_point):
    print("3points",v1, v2, common_point)
    v1=[Decimal(v1["x"]),Decimal(v1["y"])]
    v2=[Decimal(v2["x"]),Decimal(v2["y"])]
    common_point=[Decimal(common_point["x"]),Decimal(common_point["y"])]
    p1=[v1[0]-common_point[0],v1[1]-common_point[1]]
    p2=[v2[0]-common_point[0],v2[1]-common_point[1]]

    angle=calculateAngle(p1,p2)
    if angle<0:
        return -1
    else:
        return 1

def calculateAngle(v1,v2):
    return v1[0]*v2[1] - v1[1]*v2[0]

def setNewTagToWay(way,data,osmdata):
    d=''
    print(data)

def makeLaneString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way):
    turn_lanes=[]
    for i in range(0,noof_lanes_in_current_way):
        turn_lanes.append("")

    if lane_side==-1:
            for i in range(lane_difference,noof_lanes_in_current_way):
                turn_lanes[i]="through"
            if lane_difference==0:
                turn_lanes[0]+=";slight_left"
            else:
                for i in range(0,lane_difference):
                    turn_lanes[i]="slight_left"                  

    if lane_side==1:
        for i in range(0,noof_lanes_in_continous_way):
            turn_lanes[i]="through"
        if lane_difference==0:
            turn_lanes[noof_lanes_in_current_way-1]+=";slight_right"
        else:
            for i in range(0,lane_difference):
                turn_lanes[noof_lanes_in_current_way-1-i]+="slight_right"
    
    return turn_lanes

def makeConnectionString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way):
    connectors={"A-AC":[],"A-B":[]}
    if lane_side==1:
        for i in range(0,noof_lanes_in_continous_way-1):
            if i==noof_lanes_in_continous_way-1:
                connectors["A-AC"].append("{}R-{}L".format(i,i))
            else:
                connectors["A-AC"].append("{}R-{}R".format(i,i))
    if lane_side==-1:
        temp_list=[0,1,2,3,4,5,6]
        temp_index=0
        for i in range(lane_difference,noof_lanes_in_current_way-1):
            if i==0:
                connectors["A-AC"].append("{}R-{}L".format(i,temp_index))
                temp_index+=1
            else:
                connectors["A-AC"].append("{}R-{}L".format(i,temp_index))
                temp_index+=1

    if lane_difference>0 and lane_side==1:
        temp_list=[0,1,2,3,4,5,6]
        temp_index=0
        for i in range(noof_lanes_in_continous_way-1,noof_lanes_in_current_way-1):
            connectors["A-B"].append("{}R-{}L".format(i,str(temp_index)))
            temp_index+=1
    
    if lane_difference>0 and lane_side==-1:
        for i in range(0,lane_difference):
            connectors["A-B"].append("{}R-{}R".format(i,i))  
    return connectors

def addTurnLanes(osmdata,ways,start_points,nodes):
    print(len(ways))
    for way in ways:
        current_way=way
        points_in_current_way=getPointsInTheWay(current_way,False)
        for point_no,point in enumerate(points_in_current_way):
            current_point=point
            if point_no==0:
                continue
            elif point_no==len(points_in_current_way)-1:
                ways_start_from_current_point=findWaysStartAtThisPoint(start_points,current_point)
                no_of_ways_start_from_current_point=len(ways_start_from_current_point)
                if no_of_ways_start_from_current_point==2:
                    con_and_non_con_ways=findContinuationAndNonContinousPoint(ways_start_from_current_point,current_way)
                    if con_and_non_con_ways!=None:
                        continous_way=con_and_non_con_ways["continous_way"]
                        non_continous_way=con_and_non_con_ways["non_continous_way"]
                        noof_lanes_in_continous_way=findNoOfLanes(continous_way)
                        noof_lanes_in_non_continous_way=findNoOfLanes(non_continous_way)
                        noof_lanes_in_current_way=findNoOfLanes(current_way)
                        point_A=findAPoint(continous_way,nodes,1)
                        point_B=findAPoint(non_continous_way,nodes,1)
                        common_point=findAPoint(current_way,nodes,point_no)

                        if noof_lanes_in_continous_way>noof_lanes_in_current_way:
                            noof_lanes_in_continous_way=noof_lanes_in_current_way

                        lane_difference=noof_lanes_in_current_way-noof_lanes_in_continous_way
                        lane_side=getLaneSide(point_A,point_B,common_point)
                        turn_lanes=makeLaneString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way)
                        connectors=makeConnectionString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way)
                             
                        for tag in way.getElementsByTagName('tag'):
                            if(tag.getAttribute('k')=="turn:lanes"):
                                print(tag.getAttribute('v'))
                                break
                        print(noof_lanes_in_current_way)
                        print(noof_lanes_in_continous_way)
                        print(connectors)
                        setNewTagToWay(current_way, turn_lanes, osmdata)
                        
            else:
                ways_start_from_current_point=findWaysStartAtThisPoint(start_points,current_point)
                no_of_ways_start_from_current_point=len(ways_start_from_current_point)
                if no_of_ways_start_from_current_point==1:
                        continous_way=current_way
                        non_continous_way=ways_start_from_current_point[0]
                        noof_lanes_in_continous_way=findNoOfLanes(continous_way)
                        noof_lanes_in_non_continous_way=findNoOfLanes(non_continous_way)
                        noof_lanes_in_current_way=findNoOfLanes(current_way)
                        point_A=findAPoint(continous_way,nodes,point_no+1)
                        point_B=findAPoint(non_continous_way,nodes,1)
                        common_point=findAPoint(current_way,nodes,point_no)
                        if noof_lanes_in_continous_way>noof_lanes_in_current_way:
                            noof_lanes_in_continous_way=noof_lanes_in_current_way
                        lane_difference=noof_lanes_in_current_way-noof_lanes_in_continous_way
                        lane_side=getLaneSide(point_A,point_B,common_point)
                        turn_lanes=makeLaneString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way)
                        connectors=makeConnectionString(lane_difference,lane_side,noof_lanes_in_current_way,noof_lanes_in_continous_way)
                        for tag in way.getElementsByTagName('tag'):
                            if(tag.getAttribute('k')=="turn:lanes"):
                                print(tag.getAttribute('v'))
                                break
                        setNewTagToWay(current_way, turn_lanes, osmdata)

                        
def main():
    data = readOsmAsXml('./stadtring_berlin.osm') #get osmdata
    highways=findHighways(data.getElementsByTagName('way')) #getallhighways
    start_points=getStartPointsOfWays(data.getElementsByTagName('way')) #get all way start point
    nodes=data.getElementsByTagName('node') #find all points
    addTurnLanes(data,highways,start_points,nodes)

if __name__ == '__main__':
    main()
    