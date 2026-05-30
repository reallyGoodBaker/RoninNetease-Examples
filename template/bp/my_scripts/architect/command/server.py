from ..core.basic import Location, compServer, serverApi
from ..core.scheduler import Future
from ..level.server import LevelServer
from ..math.vec3 import vec, tup
from ..utils.client import isPlayer
from ..core.subsystem import subsystem

def requireChunk(location, radius=16):
    def _executor(res, rej):
        if not isinstance(location, Location):
            return rej(ValueError("location must be an instance of Location"))
        pos = vec(location.pos)
        r = vec((radius, radius, radius))

        def _detector(_):
            res() if _['code'] else rej()

        result = LevelServer.chunkSource.DoTaskOnChunkAsync(
            location.dim,
            tup(pos - r),
            tup(pos + r),
            _detector
        )

        if not result:
            return rej(ValueError("invalid location"))
    return Future(_executor)


def requireChunkRect(loc1, loc2, dimId=0):
    def _executor(res, rej):
        minX = min(loc1[0], loc2[0])
        minY = min(loc1[1], loc2[1])
        minZ = min(loc1[2], loc2[2])
        maxX = max(loc1[0], loc2[0])
        maxY = max(loc1[1], loc2[1])
        maxZ = max(loc1[2], loc2[2])
        minPos = (minX, minY, minZ)
        maxPos = (maxX, maxY, maxZ)

        def _detector(_):
            res((minPos, maxPos)) if _['code'] else rej((None, None))

        result = LevelServer.chunkSource.DoTaskOnChunkAsync(
            dimId, minPos, maxPos, _detector
        )

        if not result:
            return rej(ValueError("invalid location"))
    return Future(_executor)


class command:
    @staticmethod
    def teleport(entity, location):
        # type: (str, Location) -> Future
        ftr, res, rej = Future.resolvers()
        def _teleport():
            dimComp = compServer.CreateDimension(entity)
            dimId = dimComp.GetEntityDimensionId()
            if location.dim == dimId:
                res(compServer.CreatePos(entity).SetFootPos(location.pos))
            else:
                if isPlayer(entity):
                    res(dimComp.ChangePlayerDimension(location.dim, location.pos))
                else:
                    res(dimComp.ChangeEntityDimension(location.dim, location.pos))

        future = requireChunk(location, 16)
        future.done(_teleport).expected(rej)
        return ftr
    
    @staticmethod
    def queryTopEmptySpace(location):
        # type: (Location) -> Future
        future, resolve, reject = Future.resolvers()
        def _handler():
            x, _, z = location.pos
            resolve(LevelServer.blockInfo.GetTopBlockHeight((x, z), location.dim) + 1)
        requireChunk(location).done(_handler).expected(reject)
        return future
    
    @staticmethod
    def teleportTop(entity, location):
        # type: (str, Location) -> Future
        _future, resolve, reject = Future.resolvers()
        def _teleport():
            dimComp = compServer.CreateDimension(entity)
            dimId = dimComp.GetEntityDimensionId()
            x, _, z = location.pos
            topY = LevelServer.blockInfo.GetTopBlockHeight((x, z), location.dim)
            pos = (x, topY + 1, z)
            if location.dim == dimId:
                resolve(compServer.CreatePos(entity).SetFootPos(pos))
            else:
                if isPlayer(entity):
                    resolve(dimComp.ChangePlayerDimension(location.dim, pos))
                else:
                    resolve(dimComp.ChangeEntityDimension(location.dim, pos))

        future = requireChunk(location, 16)
        future.done(_teleport).expected(reject)
        return _future
    
    @staticmethod
    def setBlock(location, blockId, updateNeighbors=False):
        ftr, res, rej = Future.resolvers()
        requireChunk(location, 16).done(lambda: res(LevelServer.blockInfo.SetBlockNew(location.pos, { 'name': blockId }, dimensionId=location.dim, updateNeighbors=updateNeighbors))).expected(rej)
        return ftr

    @staticmethod
    def fillBlocks(pos1, pos2, blockId, dimId=0, updateNeighbors=False, chunkSize=256):
        ftr, resolve, reject = Future.resolvers()
        def _filler(rect):
            pos1, pos2 = rect
            minX, minY, minZ = pos1
            maxX, maxY, maxZ = pos2
            i = 0
            for x in range(minX, maxX + 1):
                for y in range(minY, maxY + 1):
                    for z in range(minZ, maxZ + 1):
                        LevelServer.blockInfo.SetBlockNew((x, y, z), { 'name': blockId }, dimensionId=dimId, updateNeighbors=updateNeighbors)
                        i += 1
                        if i >= chunkSize:
                            i = 0
                            yield
        def _handleFill(rect):
            serverApi.StartCoroutine(_filler(rect), resolve)
        requireChunkRect(pos1, pos2, dimId).done(_handleFill).expected(reject)
        return ftr
    
    @staticmethod
    def placeStructure(location, structureName, rot=0, mirror=0, integrity=1, loadingRadius=16):
        ftr, resolve, reject = Future.resolvers()
        def _place():
            resolve(LevelServer.game.PlaceStructure(None, location.pos, structureName, location.dim, rot, mirrorMode=mirror, integrity=integrity))
        requireChunk(location, loadingRadius).done(_place).expected(reject)
        return ftr
    
    @staticmethod
    def spawnEntity(template, location, rot, isNpc=False, isGlobal=False):
        ftr, resolve, reject = Future.resolvers()
        requireChunk(location, 16).done(lambda: resolve(subsystem.spawnServerEntity(template, location, rot, isNpc, isGlobal))).expected(reject)
        return ftr
