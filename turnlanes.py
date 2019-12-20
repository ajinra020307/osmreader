import xml.dom.minidom
from decimal import Decimal
def readOsmAsXml(osmfilepath):
    data=xml.dom.minidom.parse(osmfilepath)
    return data

def setNewTagToWay(way,data,osmdata):
    d=''
    print(data)
    for value in data:
        if d=="":
            d=value
        else:
            d+='|{v}'.format(v=value)
    print("setting connection string for way " + str(way))
    element = osmdata.createElement('tag')
    element.setAttribute('k',"testinglanes")
    element.setAttribute('v', d)
    way.appendChild(element)

def getStartPointsOfWays(ways,value):
    startpoints=[]
    pointss=[]
    for wayno,way in enumerate(ways):
        wayid=way.getAttribute('id')
        points=way.getElementsByTagName('nd')
        startpoints.append({"point":points[0].getAttribute('ref'),"wayid":wayid,'way':way})
        pointss.append(points[0].getAttribute('ref'))
    if value:
        return pointss
    return startpoints

def getHighWaysFromWays(ways):
    highways=[]
    for way in ways:
        tags=way.getElementsByTagName('tag')
        h=False
        n=False
        has_turn_lanes=False
        hv = ["primary", "motorway_link", "motorway"]
        #in primary we does not handle the condition where the turn lanes are on the right and left
        for tag in tags:
            if(tag.getAttribute('k')=="turn:lanes"):
                has_turn_lanes=True

        if True:#if it does not had turn lanes add the highway
            for tag in tags:
                if tag.getAttribute('k')=="highway" and tag.getAttribute('v') in hv:
                    h=True
                if tag.getAttribute('k')=='name' or tag.getAttribute('k')=='reg_name':
                    n=True
                if h and n:
                    highways.append(way)
                    break

    return highways

def getPointsInaWay(way,fullnodereq):
    nodes=[]
    fullnodes=[]
    points = way.getElementsByTagName('nd')
    for point in points:
        fullnodes.append(point)
        nodes.append(point.getAttribute('ref'))
    if fullnodereq:
        return fullnodes
    return nodes

def findWaysStartAtThisPoint(startpoints,curpoint,curwayid):
    ways=[]
    count=0
    for startpoint in startpoints:
        if curpoint==startpoint["point"]:
            count=count+1
            ways.append(startpoint['way'])
    return ways

def findContinuationPoint(ways,mainway):
    mainname=None
    data=[0]
    data[0]=mainway.getAttribute('id')
    for node in mainway.getElementsByTagName('tag'):
        if node.getAttribute('k')=='name':
            mainname=node.getAttribute('v')
            data.append(mainname)
        elif node.getAttribute('k')=='reg_name':
            mainname = node.getAttribute('v')
            data.append(mainname)

    if mainname:
        for i,way in enumerate(ways):
            for ni,nde in enumerate(way.getElementsByTagName('tag')):
                if nde.getAttribute('k')=='name' and nde.getAttribute('v')==mainname:
                    cway=way
                    if i==0:
                        ncway=ways[1]
                        return {"cway": cway, "ncway": ncway}
                    elif i==1:
                        ncway=ways[0]
                        return {"cway": cway, "ncway": ncway}
                elif nde.getAttribute('k')=='reg_name' and nde.getAttribute('v')==mainname:
                    cway = way
                    if i == 0:
                        ncway = ways[1]
                        return {"cway": cway, "ncway": ncway}
                    elif i == 1:
                        ncway = ways[0]
                        return {"cway": cway, "ncway": ncway}

    else:
        raise KeyError

def findNextPoint(way,osmdata):
    nodes=way.getElementsByTagName('nd')
    for i,node in enumerate(nodes):
        if(i==0):
            continue
        else:
            ref=node.getAttribute('ref')
            points=osmdata.getElementsByTagName('node')
            for point in points:
                if point.getAttribute('id')==ref:
                    lat=point.getAttribute('lat')
                    long=point.getAttribute('lon')
                    return {"x":lat,"y":long}

def getLaneSide(v1,v2,commonpoint):
    print("3points",v1, v2, commonpoint)
    v1=[Decimal(v1["x"]),Decimal(v1["y"])]
    v2=[Decimal(v2["x"]),Decimal(v2["y"])]
    commonpoint=[Decimal(commonpoint[0]),Decimal(commonpoint[1])]
    p1=[v1[0]-commonpoint[0],v1[1]-commonpoint[1]]
    p2=[v2[0]-commonpoint[0],v2[1]-commonpoint[1]]

    angle=calculateAngle(p1,p2)
    if angle<0:
        return -1
    else:
        return 1

def findNoOfLanes(way):
    tags=way.getElementsByTagName('tag')
    for tag in tags:
        if tag.getAttribute('k')=="lanes":
            return int(tag.getAttribute('v'))
    else:
        return 1

def findWaysGotSplitted(osmdata):
    ways=getHighWaysFromWays(osmdata.getElementsByTagName('way')) #all highways
    startpoints=getStartPointsOfWays(osmdata.getElementsByTagName('way'),False) #all the start point of ways
    for wayno,way in enumerate(ways):
        addTurnLanes(way,startpoints,osmdata)

def calculateAngle(v1,v2):
    return v1[0]*v2[1] - v1[1]*v2[0]

def findFirstPoint(point,osmdata):
    nodes=osmdata.getElementsByTagName('node')
    for node in nodes:
        if node.getAttribute('id')==point:
            lat=node.getAttribute('lat')
            lon=node.getAttribute('lon')
            return [lat,lon]

def addTurnLanes(way,startpoints,osmdata):
    wayid = way.getAttribute('id')
    points = getPointsInaWay(way, False)
    wayswherepointisstart = findWaysStartAtThisPoint(startpoints, points[len(points) - 1], wayid)
    noofroadssplitted = len(wayswherepointisstart)
    if noofroadssplitted == 2:
        candncpoints = findContinuationPoint(wayswherepointisstart, way)
        if candncpoints:
                conway = candncpoints["cway"]
                nconway = candncpoints["ncway"]
                pointA = findNextPoint(conway,osmdata)
                pointB = findNextPoint(nconway,osmdata)

                commonpoint=findFirstPoint(points[len(points) - 1],osmdata)
                laneside = getLaneSide(pointA,pointB,commonpoint)
                nooflanesincway = findNoOfLanes(way)
                nooflanesinconway = findNoOfLanes(conway)
                nooflanesin_turningway=findNoOfLanes(nconway)

                if nooflanesinconway > nooflanesincway:
                    nooflanesinconway=nooflanesincway

                lanedifference = nooflanesincway - nooflanesinconway
                l = []

                if laneside == -1:
                    for i in range(nooflanesincway):
                        l.append("")
                    for i in range(lanedifference, nooflanesincway):
                        l[i]="through"

                    if lanedifference == 0:
                        l[0] += ";slight_left"
                    else:
                        for i in range(0, lanedifference):
                            l[i] += ";slight_left"

                elif laneside == 1:
                    for i in range(nooflanesincway):
                        l.append("")
                    for i in range(0, nooflanesinconway):
                        l[i]="through"

                    if lanedifference == 0:
                        l[nooflanesinconway - 1] += ';slight_right'
                    else:
                        for i in range(0, lanedifference):
                                l[nooflanesincway - 1 - i] += ";slight_right"


                print("id",way.getAttribute('id'))
                for tag in way.getElementsByTagName('tag'):
                    if(tag.getAttribute('k')=="turn:lanes"):
                        print(tag.getAttribute('v'))
                        break

                setNewTagToWay(way, l, osmdata)

def findWaysSplittedFromMiddle(osmdata):
    ways = getHighWaysFromWays(osmdata.getElementsByTagName('way'))  # all highways
    startpoints = getStartPointsOfWays(osmdata.getElementsByTagName('way'), False)
    for way in ways:
        wayid=way.getAttribute('id')
        points=getPointsInaWay(way,False)
        for i,point in enumerate(points):
            if i==len(points)-1:
                break
            elif i==0:
                continue
            wayswherepointisstart=findWaysStartAtThisPoint(startpoints, point, wayid)
            if(len(wayswherepointisstart)==1):
                        cway = way
                        ncway = wayswherepointisstart[0]
                        pointA = findNextPoint(cway, osmdata)
                        pointB = findNextPoint(ncway, osmdata)
                        commonpoint = findFirstPoint(point, osmdata)
                        laneside = getLaneSide(pointA, pointB, commonpoint)
                        nooflanesincway = findNoOfLanes(way)
                        nooflanesinconway = findNoOfLanes(cway)
                        if nooflanesinconway > nooflanesincway:
                           nooflanesinconway=nooflanesincway

                        lanedifference = nooflanesincway - nooflanesinconway
                        l = []
                        if laneside == -1:
                            for i in range(lanedifference, nooflanesincway):
                                l.append("through")
                            if lanedifference == 0:
                                l[0] += ":slight_left"
                            else:
                                for i in range(0, lanedifference):
                                    l[i] += ":slight_left"

                        elif laneside == 1:
                            for i in range(0, nooflanesinconway):
                                l.append("through")
                            if lanedifference == 0:
                                l[nooflanesinconway - 1] += ';slight_right'
                            else:
                                for i in range(nooflanesinconway, nooflanesincway):
                                    l.append("slight_right")
                                # for i in range(0, lanedifference):
                                #     l[nooflanesinconway - 1 - i] += ";slight_right"

                        print("id",way.getAttribute('id'))
                        for tag in way.getElementsByTagName('tag'):
                            if (tag.getAttribute('k') == "turn:lanes"):
                                print(tag.getAttribute('v'))
                                break

                        setNewTagToWay(way, l, osmdata)

    with open("neeelanetest4.osm", "w+", encoding='utf-8') as xml_file:
        print("writing data to new file")
        osmdata.writexml(xml_file)



def main():
    data = readOsmAsXml('./stadtring_berlin.osm')
    findWaysGotSplitted(data)
    findWaysSplittedFromMiddle(data)

if __name__ == '__main__':
    main()
