import Link from 'next/link';

const Navbar = () => {
    return (
        <nav className="bg-gray-800 p-4 text-white flex justify-between">
            <div className="flex items-center space-x-4">
                <Link className="hover:bg-gray-700 px-3 py-2 rounded" href="/">
                    Home
                </Link>
                <Link href="/upload" className="hover:bg-gray-700 px-3 py-2 rounded">
                    Upload
                </Link>
                <Link href="/docs" className="hover:bg-gray-700 px-3 py-2 rounded">
                    Documents
                </Link>
                
            </div>
        </nav>
    );
};

export default Navbar;



