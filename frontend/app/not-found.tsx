import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-4 text-center">
      <p className="text-7xl font-bold text-primary-600 mb-4">404</p>
      <h1 className="text-2xl font-bold text-white mb-2">
        페이지를 찾을 수 없습니다
      </h1>
      <p className="text-gray-400 mb-8 max-w-md">
        요청하신 페이지가 존재하지 않거나 이동되었습니다.
      </p>
      <Link
        href="/"
        className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
      >
        홈으로 돌아가기
      </Link>
    </div>
  );
}
