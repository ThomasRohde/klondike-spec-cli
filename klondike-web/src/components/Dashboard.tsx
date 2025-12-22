export function Dashboard() {
    return (
        <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Features</h3>
                    <p className="text-4xl font-bold text-indigo-600">76</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Verified</h3>
                    <p className="text-4xl font-bold text-green-600">45</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">In Progress</h3>
                    <p className="text-4xl font-bold text-yellow-600">1</p>
                </div>
            </div>
            <div className="mt-8 bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Progress</h3>
                <div className="w-full bg-gray-200 rounded-full h-4">
                    <div className="bg-indigo-600 h-4 rounded-full" style={{ width: '59.2%' }}></div>
                </div>
                <p className="text-sm text-gray-600 mt-2">59.2% Complete</p>
            </div>
        </div>
    )
}
